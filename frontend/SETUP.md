# Frontend Setup and Testing Instructions

## 🚀 Quick Start

### 1. Start Backend Server
```bash
cd RAG_System
python main.py
```
Backend will run on: http://localhost:8000

### 2. Start Frontend Development Server
```bash
cd frontend
npm start
```
Frontend will run on: http://localhost:3000

## 📋 Features Implemented (Phase 1-3)

### ✅ CORS Configuration
- Backend configured to accept requests from http://localhost:3000
- All HTTP methods and headers allowed

### ✅ React + Tailwind Setup
- Create React App with TypeScript
- Tailwind CSS configured with custom theme
- Professional color scheme and responsive design

### ✅ Document Upload Component
- **Drag & Drop Support**: Visual feedback during file drag
- **File Validation**: Only accepts .txt files
- **Progress Indicators**: Loading states during upload
- **Success/Error Handling**: Clear user feedback
- **Chunk Information**: Displays word count and chunk count after upload

### ✅ API Integration
- Service layer for backend communication
- TypeScript interfaces for type safety
- Error handling and response validation
- Integration with `/store-chunks` endpoint

## 🎯 Testing the Document Upload

1. **Create a test file**: Create a `.txt` file with sample content
2. **Upload via drag & drop**: Drag the file onto the upload area
3. **Or use file browser**: Click "Browse Files" to select
4. **View results**: See chunk count and processing information

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── DocumentUpload.tsx    # Main upload component
│   │   └── index.ts              # Component exports
│   ├── services/
│   │   └── api.ts                # API service layer
│   ├── App.tsx                   # Main application
│   └── index.css                 # Tailwind CSS setup
├── tailwind.config.js            # Tailwind configuration
├── postcss.config.js             # PostCSS configuration
└── package.json                  # Dependencies
```

## 🔧 Technical Details

### API Endpoints Used
- `POST /store-chunks` - Document upload and processing
- `GET /health` - Backend health check
- `GET /store-stats` - Vector database statistics

### Component Features
- **File Validation**: Ensures only .txt files are accepted
- **Visual Feedback**: Drag states, loading indicators, success/error messages
- **Responsive Design**: Works on desktop browsers
- **Type Safety**: Full TypeScript support

## 🚨 Known Issues
- Tailwind CSS warnings in IDE (expected, will resolve on build)
- Backend server must be running for frontend to function properly

## 🎨 Design Features
- Professional UI with Tailwind CSS
- Smooth transitions and hover effects
- Clear visual hierarchy
- Accessibility considerations
- Recruiter-friendly interface

## 📝 Next Steps (Future Phases)
- Chat interface component
- Retrieved chunks display
- Metrics dashboard
- Hallucination indicators
- Real-time streaming with Socket.IO
