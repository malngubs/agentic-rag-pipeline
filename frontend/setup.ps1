# ============================================================================
# 🚀 MACROCOMM BI PLATFORM - FRONTEND SETUP (Windows PowerShell)
# ============================================================================
# 
# Run this script in PowerShell to set up the frontend.
# Make sure you have Node.js 18+ installed.

Write-Host ""
Write-Host "🚀 MACROCOMM BI PLATFORM - FRONTEND SETUP" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Node.js version
Write-Host "📋 Checking Node.js version..." -ForegroundColor Yellow
$nodeVersion = node --version 2>$null
if (-not $nodeVersion) {
    Write-Host "❌ Node.js is not installed. Please install Node.js 18+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Node.js version: $nodeVersion" -ForegroundColor Green

# Step 1: Install dependencies
Write-Host ""
Write-Host "📦 Step 1: Installing dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Step 2: Create .env.local if it doesn't exist
Write-Host ""
Write-Host "🔐 Step 2: Setting up environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env.local")) {
    Copy-Item ".env.example" ".env.local"
    Write-Host "✅ Created .env.local from .env.example" -ForegroundColor Green
} else {
    Write-Host "✅ .env.local already exists" -ForegroundColor Green
}

# Step 3: Type check
Write-Host ""
Write-Host "🔍 Step 3: Running type check..." -ForegroundColor Yellow
npm run type-check 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Type check passed" -ForegroundColor Green
} else {
    Write-Host "⚠️ Type check had some issues (this is okay for first run)" -ForegroundColor Yellow
}

# Done!
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🎉 SETUP COMPLETE!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor White
Write-Host "   1. Make sure your backend is running at http://localhost:8000" -ForegroundColor Gray
Write-Host "   2. Run: npm run dev" -ForegroundColor Gray
Write-Host "   3. Open: http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 Available commands:" -ForegroundColor White
Write-Host "   npm run dev        - Start development server" -ForegroundColor Gray
Write-Host "   npm run build      - Build for production" -ForegroundColor Gray
Write-Host "   npm run start      - Start production server" -ForegroundColor Gray
Write-Host "   npm run lint       - Run linter" -ForegroundColor Gray
Write-Host "   npm run type-check - Run TypeScript check" -ForegroundColor Gray
Write-Host ""
