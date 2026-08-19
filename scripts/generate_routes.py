import os
from pathlib import Path

routes = [
    "dashboard",
    "projects",
    "projects/[id]",
    "projects/[id]/targets",
    "projects/[id]/targets/[target_id]",
    "projects/[id]/harnesses",
    "projects/[id]/corpus",
    "projects/[id]/campaigns",
    "projects/[id]/campaigns/[campaign_id]",
    "projects/[id]/coverage",
    "projects/[id]/crashes",
    "projects/[id]/crashes/[crash_id]",
    "projects/[id]/findings",
    "projects/[id]/reports",
    "projects/[id]/evidence",
    "settings"
]

base_path = Path("../frontend/src/app")

if not base_path.exists():
    base_path = Path("../frontend/app") # Try without src/ just in case

for route in routes:
    route_path = base_path / route
    route_path.mkdir(parents=True, exist_ok=True)
    
    page_file = route_path / "page.tsx"
    
    # Create a simple component based on the route name
    component_name = "Page"
    title = f"/{route}"
    
    content = f"""export default function {component_name}() {{
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">{title}</h1>
      <p className="text-gray-500">This page is under construction.</p>
    </div>
  );
}}
"""
    if not page_file.exists():
        with open(page_file, "w") as f:
            f.write(content)
        print(f"Created {page_file}")

print("Routes generated.")
