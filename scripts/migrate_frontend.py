import os
import shutil

# Paths
VITE_SRC = "d:\\Codec Technologies\\Aetherguard\\client\\src"
NEXT_APP = "d:\\Codec Technologies\\Aetherguard\\landing\\src\\app"
NEXT_COMPONENTS = "d:\\Codec Technologies\\Aetherguard\\landing\\src\\components"
NEXT_GLOBAL_CSS = "d:\\Codec Technologies\\Aetherguard\\landing\\src\\app\\globals.css"

# 1. Create Dashboard App Route
dashboard_dir = os.path.join(NEXT_APP, "dashboard")
os.makedirs(dashboard_dir, exist_ok=True)

# 2. Copy components
dest_components = os.path.join(NEXT_COMPONENTS, "dashboard")
os.makedirs(dest_components, exist_ok=True)

for file in os.listdir(os.path.join(VITE_SRC, "components")):
    if file.endswith(".jsx"):
        src = os.path.join(VITE_SRC, "components", file)
        dst = os.path.join(dest_components, file.replace(".jsx", ".tsx"))
        
        with open(src, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Add 'use client' and fix imports
        content = "'use client';\n\n" + content
        content = content.replace('class=', 'className=')  # Just in case
        
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(content)

# 3. Create Dashboard Page (Translating App.jsx)
with open(os.path.join(VITE_SRC, "App.jsx"), 'r', encoding='utf-8') as f:
    app_content = f.read()

# Fix component imports in App.jsx
app_content = app_content.replace("'./components/", "'@/components/dashboard/")
app_content = "'use client';\n\n" + app_content

with open(os.path.join(dashboard_dir, "page.tsx"), 'w', encoding='utf-8') as f:
    f.write(app_content.replace('function App()', 'export default function DashboardPage()').replace('export default App', ''))

# 4. Integrate CSS securely
with open(os.path.join(VITE_SRC, "index.css"), 'r', encoding='utf-8') as f:
    vite_css = f.read()
with open(os.path.join(VITE_SRC, "App.css"), 'r', encoding='utf-8') as f:
    app_css = f.read()

# To avoid Tailwind global conflicts, we wrap the dashboard CSS
wrapped_css = """
/* ================================== */
/* LEGACY DASHBOARD CSS INTEGRATION   */
/* ================================== */
.dashboard-layout-wrapper {
""" + vite_css.replace('body {', 'body-disabled {').replace('root {', 'root-disabled {') + app_css + "\n}"

with open(NEXT_GLOBAL_CSS, 'a', encoding='utf-8') as f:
    f.write(wrapped_css)

print("Migration script executed successfully.")
