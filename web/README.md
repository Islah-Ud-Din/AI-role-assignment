# SEO Article Generator - Web UI

A modern Next.js web interface for the SEO Article Generation Platform.

## Features

- 🎨 **Modern UI**: Beautiful, responsive interface built with Tailwind CSS
- 📊 **Real-time Status**: Live job progress tracking with visual indicators
- 📝 **Article Display**: Rich article viewer with SEO metrics, keyword analysis, and quality scores
- 📋 **Job Management**: View and manage all article generation jobs
- 🔄 **Auto-refresh**: Automatic polling for job status updates
- 🌙 **Dark Mode**: Built-in dark mode support

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- The FastAPI backend running on `http://localhost:8000` (or configure `NEXT_PUBLIC_API_URL`)

### Installation

1. Navigate to the web directory:
```bash
cd web
```

2. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

3. Configure the API URL (optional):
   - Create or edit `.env.local` file
   - Set `NEXT_PUBLIC_API_URL=http://localhost:8000` (or your backend URL)

4. Start the development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
web/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main dashboard page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── JobForm.tsx        # Article creation form
│   ├── JobList.tsx        # List of all jobs
│   ├── JobStatusTracker.tsx  # Job progress tracker
│   └── ArticleDisplay.tsx    # Article viewer with tabs
├── lib/                   # Utilities
│   └── api.ts             # API client functions
├── types/                 # TypeScript types
│   └── api.ts             # API type definitions
└── package.json          # Dependencies and scripts
```

## Usage

### Creating an Article

1. Enter a topic/keyword in the form
2. Optionally adjust word count and language
3. Click "Generate Article"
4. Watch the progress in real-time
5. View the completed article with SEO metrics

### Viewing Jobs

- All jobs are listed in the left sidebar
- Click any job to view its details
- Failed jobs can be resumed using the resume button
- Jobs automatically refresh every 2 seconds while in progress

### Article Display

The article viewer has four tabs:

1. **Content**: Full article with sections and SEO metadata
2. **SEO Metrics**: Quality scores, validation results, and keyword analysis
3. **Links**: Internal linking suggestions and external references
4. **FAQ**: Generated FAQ section

## Building for Production

```bash
npm run build
npm start
```

## Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)

## Technologies Used

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library
- **Axios**: HTTP client
- **date-fns**: Date formatting utilities

## Development

The UI automatically connects to the FastAPI backend. Make sure the backend is running before starting the Next.js dev server.

For development with hot reload:
```bash
npm run dev
```

## Troubleshooting

### API Connection Issues

- Ensure the FastAPI backend is running
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify CORS is enabled on the backend (should be configured to allow `*`)

### Build Errors

- Clear `.next` directory: `rm -rf .next`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
