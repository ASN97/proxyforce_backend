from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the role-based routers
from routers import project_manager, sales_executive, marketing_executive
from routers import projects  # 👈 make sure this matches your filename




app = FastAPI(title="ProxyForce Backend")

# CORS setup so React frontend can talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(project_manager.router, tags=["Project Manager"])
app.include_router(sales_executive.router, tags=["Sales Executive"])
app.include_router(marketing_executive.router, tags=["Marketing Executive"])
app.include_router(projects.router)

@app.get("/")
def root():
    return {"message": "ProxyForce backend is running"}
