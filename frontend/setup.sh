#!/bin/bash
# ============================================================================
# 🚀 MACROCOMM BI PLATFORM - FRONTEND SETUP SCRIPT
# ============================================================================
# 
# This script sets up the Next.js frontend for the Macrocomm BI Platform.
# Run this in PowerShell or bash after downloading the frontend files.

echo "🚀 Setting up Macrocomm BI Platform Frontend..."
echo ""

# Step 1: Create Next.js project
echo "📦 Step 1: Creating Next.js project..."
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir=false --import-alias "@/*"

cd frontend

# Step 2: Install core dependencies
echo "📦 Step 2: Installing core dependencies..."
npm install zustand @tanstack/react-query framer-motion

# Step 3: Install UI dependencies
echo "🎨 Step 3: Installing UI dependencies..."
npm install lucide-react class-variance-authority clsx tailwind-merge

# Step 4: Install chart dependencies
echo "📊 Step 4: Installing chart dependencies..."
npm install @tremor/react recharts

# Step 5: Install form and validation
echo "📝 Step 5: Installing form dependencies..."
npm install react-hook-form @hookform/resolvers zod

# Step 6: Install dashboard grid
echo "📐 Step 6: Installing dashboard grid..."
npm install react-grid-layout

# Step 7: Install additional utilities
echo "🔧 Step 7: Installing utilities..."
npm install date-fns react-markdown react-syntax-highlighter

# Step 8: Install animation plugin
echo "✨ Step 8: Installing animation plugin..."
npm install tailwindcss-animate

# Step 9: Install Zustand middleware
echo "🗄️ Step 9: Installing Zustand middleware..."
npm install immer

# Step 10: Install dev dependencies
echo "🛠️ Step 10: Installing dev dependencies..."
npm install -D @types/react-grid-layout

# Step 11: Initialize shadcn/ui
echo "🎨 Step 11: Initializing shadcn/ui..."
npx shadcn-ui@latest init -y

# Step 12: Add shadcn components
echo "🧩 Step 12: Adding shadcn components..."
npx shadcn-ui@latest add button card input dialog dropdown-menu toast avatar badge separator scroll-area tabs tooltip sheet

echo ""
echo "✅ Frontend setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Copy the downloaded frontend files to the 'frontend' folder"
echo "   2. Create a .env.local file with your API URL:"
echo "      NEXT_PUBLIC_API_URL=http://localhost:8000"
echo "      NEXT_PUBLIC_WS_URL=ws://localhost:8000"
echo "   3. Run: npm run dev"
echo "   4. Open: http://localhost:3000"
echo ""
