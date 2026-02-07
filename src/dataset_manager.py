"""
================================================================================
UNIFIED DATASET MANAGER - MACROCOMM BI PLATFORM
================================================================================

Central service for managing datasets across all BI Platform features.
Upload once, use everywhere (Chat, Analysis, NL Query, Transform, etc.)

ARCHITECTURE:
=============
                    ┌─────────────────────────────────────┐
                    │       DATASET MANAGER               │
                    │   (Central Data Orchestrator)       │
                    └─────────────────┬───────────────────┘
                                      │
        ┌─────────────┬───────────────┼───────────────┬─────────────┐
        ▼             ▼               ▼               ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐
   │   Raw   │  │ DataFrame│  │   Vector    │  │ Metadata │  │  Active  │
   │  Files  │  │  Store   │  │   Store     │  │   Store  │  │ Dataset  │
   └─────────┘  └──────────┘  └─────────────┘  └──────────┘  └──────────┘

USAGE:
======
    from dataset_manager import DatasetManager, dataset_manager

    # Upload a dataset (processes for all features)
    dataset = await dataset_manager.upload_dataset(file, filename)

    # Set active dataset
    dataset_manager.set_active_dataset(dataset_id)

    # Get data for different purposes
    df = dataset_manager.get_dataframe(dataset_id)  # For Analysis
    context = await dataset_manager.search_context(query)  # For Chat/RAG
    metadata = dataset_manager.get_metadata(dataset_id)  # For info display

Author: Macrocomm Development Team
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from io import BytesIO

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatasetManager")


# =============================================================================
# DATA CLASSES
# =============================================================================

class DatasetStatus(Enum):
    """Dataset processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


@dataclass
class ColumnMetadata:
    """Metadata for a single column"""
    name: str
    dtype: str
    non_null_count: int
    null_count: int
    unique_count: int
    sample_values: List[Any]
    # Numeric columns
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_value: Optional[float] = None
    # Categorical columns
    top_values: Optional[List[Tuple[str, int]]] = None


@dataclass
class DatasetMetadata:
    """Complete metadata for a dataset"""
    id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    upload_time: str
    status: DatasetStatus
    row_count: int = 0
    column_count: int = 0
    columns: List[ColumnMetadata] = field(default_factory=list)
    sheets: List[str] = field(default_factory=list)  # For Excel files
    vector_chunks: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "upload_time": self.upload_time,
            "status": self.status.value,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": [
                {
                    "name": c.name,
                    "dtype": c.dtype,
                    "non_null_count": c.non_null_count,
                    "null_count": c.null_count,
                    "unique_count": c.unique_count,
                    "sample_values": c.sample_values[:5],
                    "min_value": c.min_value,
                    "max_value": c.max_value,
                    "mean_value": c.mean_value,
                    "top_values": c.top_values[:5] if c.top_values else None,
                }
                for c in self.columns
            ],
            "sheets": self.sheets,
            "vector_chunks": self.vector_chunks,
            "error_message": self.error_message,
        }


# =============================================================================
# DATASET MANAGER
# =============================================================================

class DatasetManager:
    """
    Unified dataset manager for the BI Platform.
    Handles storage, retrieval, and processing of datasets across all features.
    """

    def __init__(self, storage_dir: str = "./data/datasets"):
        """Initialize the DatasetManager"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory stores
        self._datasets: Dict[str, DatasetMetadata] = {}
        self._dataframes: Dict[str, pd.DataFrame] = {}
        self._active_dataset_id: Optional[str] = None

        # RAG system reference (set externally)
        self._rag_system = None

        logger.info(f"DatasetManager initialized. Storage: {self.storage_dir}")

    def set_rag_system(self, rag_system):
        """Set the RAG system for vector operations"""
        self._rag_system = rag_system
        logger.info("RAG system connected to DatasetManager")

    # =========================================================================
    # UPLOAD & PROCESSING
    # =========================================================================

    async def upload_dataset(
        self,
        content: bytes,
        filename: str,
        process_for_rag: bool = True
    ) -> DatasetMetadata:
        """
        Upload and process a dataset for all features.

        Args:
            content: Raw file content
            filename: Original filename
            process_for_rag: Whether to create vector embeddings

        Returns:
            DatasetMetadata with processing results
        """
        # Generate unique ID
        dataset_id = self._generate_id(filename, content)

        # Determine file type
        extension = Path(filename).suffix.lower()
        file_type = self._get_file_type(extension)

        # Create initial metadata
        metadata = DatasetMetadata(
            id=dataset_id,
            filename=f"{dataset_id}{extension}",
            original_filename=filename,
            file_size=len(content),
            file_type=file_type,
            upload_time=datetime.now().isoformat(),
            status=DatasetStatus.PROCESSING,
        )

        self._datasets[dataset_id] = metadata
        logger.info(f"📁 Processing dataset: {filename} (ID: {dataset_id})")

        try:
            # Save raw file
            raw_path = self.storage_dir / metadata.filename
            with open(raw_path, 'wb') as f:
                f.write(content)

            # Parse to DataFrame
            df = await self._parse_to_dataframe(content, extension)

            if df is not None and not df.empty:
                self._dataframes[dataset_id] = df

                # Update metadata
                metadata.row_count = len(df)
                metadata.column_count = len(df.columns)
                metadata.columns = self._extract_column_metadata(df)

                logger.info(f"✅ Parsed {filename}: {metadata.row_count} rows, {metadata.column_count} columns")

            # Process for RAG (vector embeddings)
            if process_for_rag and self._rag_system:
                chunks_created = await self._process_for_rag(dataset_id, content, filename, df)
                metadata.vector_chunks = chunks_created
                logger.info(f"✅ Created {chunks_created} vector chunks for RAG")

            metadata.status = DatasetStatus.READY

            # Set as active if first dataset
            if self._active_dataset_id is None:
                self._active_dataset_id = dataset_id
                logger.info(f"📌 Set {filename} as active dataset")

            logger.info(f"🎉 Dataset {filename} ready for all features!")
            return metadata

        except Exception as e:
            logger.error(f"❌ Failed to process {filename}: {str(e)}")
            metadata.status = DatasetStatus.ERROR
            metadata.error_message = str(e)
            return metadata

    def _sanitize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Sanitize DataFrame column names for SQL compatibility.
        Handles unnamed columns, special characters, and duplicates.
        """
        import re

        def sanitize_column_name(col_name: str, index: int) -> str:
            """Sanitize a single column name"""
            col = str(col_name).strip()

            # Handle unnamed columns (pandas creates "Unnamed: 0", etc.)
            if col.lower().startswith('unnamed'):
                return f'column_{index}'

            # Replace problematic SQL characters with underscores
            col = re.sub(r'[:\s\-\.\(\)\[\]\{\}\+\*\/\\@#$%^&!=<>,;\'\"]+', '_', col)

            # Remove leading/trailing underscores
            col = col.strip('_')

            # Ensure doesn't start with a number
            if col and col[0].isdigit():
                col = f'col_{col}'

            # If empty, use index-based name
            if not col:
                return f'column_{index}'

            return col

        # Apply sanitization with duplicate handling
        new_columns = []
        seen_names = set()
        for i, col in enumerate(df.columns):
            sanitized = sanitize_column_name(col, i)
            if sanitized in seen_names:
                sanitized = f'{sanitized}_{i}'
            seen_names.add(sanitized)
            new_columns.append(sanitized)

        df.columns = new_columns
        return df

    async def _parse_to_dataframe(self, content: bytes, extension: str) -> Optional[pd.DataFrame]:
        """Parse file content to pandas DataFrame"""
        try:
            df = None

            if extension in ['.xlsx', '.xls']:
                # Excel file - read first sheet by default
                excel_file = pd.ExcelFile(BytesIO(content))
                df = pd.read_excel(excel_file, sheet_name=0)

                # Store sheet names in metadata
                dataset_id = list(self._datasets.keys())[-1]
                if dataset_id in self._datasets:
                    self._datasets[dataset_id].sheets = excel_file.sheet_names

            elif extension == '.csv':
                df = pd.read_csv(BytesIO(content))

            elif extension == '.json':
                df = pd.read_json(BytesIO(content))

            elif extension == '.parquet':
                df = pd.read_parquet(BytesIO(content))

            else:
                # Text-based files (PDF, DOCX, TXT) - no DataFrame
                return None

            # Sanitize column names for SQL compatibility
            if df is not None:
                df = self._sanitize_column_names(df)

            return df

        except Exception as e:
            logger.error(f"DataFrame parsing failed: {str(e)}")
            return None

    def _extract_column_metadata(self, df: pd.DataFrame) -> List[ColumnMetadata]:
        """Extract metadata for all columns"""
        columns = []

        for col in df.columns:
            col_data = df[col]
            dtype = str(col_data.dtype)

            metadata = ColumnMetadata(
                name=str(col),
                dtype=dtype,
                non_null_count=int(col_data.notna().sum()),
                null_count=int(col_data.isna().sum()),
                unique_count=int(col_data.nunique()),
                sample_values=col_data.dropna().head(10).tolist(),
            )

            # Numeric column statistics
            if pd.api.types.is_numeric_dtype(col_data):
                metadata.min_value = float(col_data.min()) if not pd.isna(col_data.min()) else None
                metadata.max_value = float(col_data.max()) if not pd.isna(col_data.max()) else None
                metadata.mean_value = float(col_data.mean()) if not pd.isna(col_data.mean()) else None
                metadata.median_value = float(col_data.median()) if not pd.isna(col_data.median()) else None
                metadata.std_value = float(col_data.std()) if not pd.isna(col_data.std()) else None

            # Categorical column top values
            if col_data.dtype == 'object' or col_data.dtype.name == 'category':
                value_counts = col_data.value_counts().head(10)
                metadata.top_values = [(str(k), int(v)) for k, v in value_counts.items()]

            columns.append(metadata)

        return columns

    async def _process_for_rag(
        self,
        dataset_id: str,
        content: bytes,
        filename: str,
        df: Optional[pd.DataFrame]
    ) -> int:
        """Process dataset for RAG (vector embeddings)"""
        if not self._rag_system:
            return 0

        try:
            # Use the existing RAG system's process_document method
            processed = await self._rag_system.process_document(Path(filename), content)

            if processed:
                # Get chunk count from RAG system
                return self._rag_system.document_metadata.get(dataset_id, {}).get('chunks', 0)
            return 0

        except Exception as e:
            logger.error(f"RAG processing failed: {str(e)}")
            return 0

    # =========================================================================
    # DATASET ACCESS
    # =========================================================================

    def get_active_dataset(self) -> Optional[DatasetMetadata]:
        """Get the currently active dataset"""
        if self._active_dataset_id and self._active_dataset_id in self._datasets:
            return self._datasets[self._active_dataset_id]
        return None

    def get_active_dataframe(self) -> Optional[pd.DataFrame]:
        """Get DataFrame for the active dataset"""
        if self._active_dataset_id and self._active_dataset_id in self._dataframes:
            return self._dataframes[self._active_dataset_id]
        return None

    def set_active_dataset(self, dataset_id: str) -> bool:
        """Set the active dataset"""
        if dataset_id in self._datasets:
            self._active_dataset_id = dataset_id
            logger.info(f"📌 Active dataset changed to: {self._datasets[dataset_id].original_filename}")
            return True
        return False

    def get_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """Get metadata for a specific dataset"""
        return self._datasets.get(dataset_id)

    def get_dataframe(self, dataset_id: str = None) -> Optional[pd.DataFrame]:
        """Get DataFrame for a dataset (defaults to active)"""
        target_id = dataset_id or self._active_dataset_id
        if target_id and target_id in self._dataframes:
            return self._dataframes[target_id]
        return None

    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all available datasets"""
        return [
            {
                **meta.to_dict(),
                "is_active": meta.id == self._active_dataset_id,
            }
            for meta in self._datasets.values()
        ]

    # =========================================================================
    # RAG / CHAT INTEGRATION
    # =========================================================================

    async def search_context(
        self,
        query: str,
        dataset_id: str = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant context in the vector store"""
        if not self._rag_system:
            return []

        try:
            # Use RAG system's search
            results = await self._rag_system.vector_store.search(
                query_text=query,
                limit=limit,
                score_threshold=0.3
            )
            return results
        except Exception as e:
            logger.error(f"Context search failed: {str(e)}")
            return []

    async def query_with_context(self, query: str, dataset_id: str = None) -> Dict[str, Any]:
        """Query using RAG with the active dataset context"""
        if not self._rag_system:
            return {"error": "RAG system not available"}

        try:
            result = await self._rag_system.query(query)
            return result
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            return {"error": str(e)}

    # =========================================================================
    # DATASET MANAGEMENT
    # =========================================================================

    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset and all its data"""
        if dataset_id not in self._datasets:
            return False

        metadata = self._datasets[dataset_id]

        # Delete raw file
        raw_path = self.storage_dir / metadata.filename
        if raw_path.exists():
            raw_path.unlink()

        # Remove from stores
        if dataset_id in self._dataframes:
            del self._dataframes[dataset_id]

        del self._datasets[dataset_id]

        # Update active if needed
        if self._active_dataset_id == dataset_id:
            self._active_dataset_id = next(iter(self._datasets.keys()), None)

        logger.info(f"🗑️ Deleted dataset: {metadata.original_filename}")
        return True

    def get_excel_sheet(self, dataset_id: str, sheet_name: str) -> Optional[pd.DataFrame]:
        """Get a specific sheet from an Excel dataset"""
        metadata = self._datasets.get(dataset_id)
        if not metadata or metadata.file_type != 'excel':
            return None

        raw_path = self.storage_dir / metadata.filename
        if not raw_path.exists():
            return None

        try:
            return pd.read_excel(raw_path, sheet_name=sheet_name)
        except Exception as e:
            logger.error(f"Failed to read sheet {sheet_name}: {str(e)}")
            return None

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def _generate_id(self, filename: str, content: bytes) -> str:
        """Generate a unique ID for a dataset"""
        hash_input = f"{filename}-{len(content)}-{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _get_file_type(self, extension: str) -> str:
        """Determine file type from extension"""
        type_map = {
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.csv': 'csv',
            '.json': 'json',
            '.parquet': 'parquet',
            '.pdf': 'pdf',
            '.docx': 'word',
            '.txt': 'text',
        }
        return type_map.get(extension, 'unknown')

    def get_stats(self) -> Dict[str, Any]:
        """Get dataset manager statistics"""
        return {
            "total_datasets": len(self._datasets),
            "active_dataset_id": self._active_dataset_id,
            "active_dataset_name": self._datasets[self._active_dataset_id].original_filename if self._active_dataset_id else None,
            "total_rows": sum(m.row_count for m in self._datasets.values()),
            "total_vector_chunks": sum(m.vector_chunks for m in self._datasets.values()),
            "storage_path": str(self.storage_dir),
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global instance for easy access
dataset_manager = DatasetManager()


def get_dataset_manager() -> DatasetManager:
    """Get the global DatasetManager instance"""
    return dataset_manager
