from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from app.api.routes import chat

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(chat.router, prefix="/api")

# Serve index page
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

if __name__ == "__main__":
    # Start the DOCX to HTML watcher in a separate process
    import multiprocessing
    from app.services.docx_to_html_service import start_watcher, convert_existing_files
    
    # Convert existing files first
    convert_existing_files("output")
    
    # Start the watcher in a separate process
    watcher_process = multiprocessing.Process(target=start_watcher, args=("output",))
    watcher_process.start()
    
    # Start the FastAPI server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    
    # Clean up the watcher process when the server stops
    watcher_process.terminate()
    watcher_process.join() 