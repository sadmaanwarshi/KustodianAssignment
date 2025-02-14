from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from io import BytesIO

# Initialize Firebase
cred = credentials.Certificate("credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://localdbtest-fab29-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

app = FastAPI()

# ✅ Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow only your React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Upload and store Excel data in Firebase
@app.post("/upload-excel/")
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        return {"error": "Invalid file format. Please upload an Excel file (.xlsx or .xls)."}

    try:
        contents = await file.read()
        excel_data = BytesIO(contents)

        df = pd.read_excel(excel_data, engine="openpyxl")

        # Convert datetime columns to string format
        for col in df.select_dtypes(include=["datetime64"]).columns:
            df[col] = df[col].astype(str)

        data_dict = df.to_dict(orient="records")

        # Store data in Firebase
        ref = db.reference("excel_data")
        ref.set(data_dict)

        return {
            "message": "Data uploaded successfully",
            "filename": file.filename,
            "columns": df.columns.tolist(),
            "sample_data": data_dict[:5]  # Show first 5 rows
        }

    except Exception as e:
        return {"error": f"Failed to process the file: {str(e)}"}

# ✅ Fetch stored data from Firebase
@app.get("/data/")
async def get_data():
    try:
        ref = db.reference("excel_data")
        data = ref.get()
        return {"data": data} if data else {"message": "No data found"}
    except Exception as e:
        return {"error": f"Failed to fetch data: {str(e)}"}

# ✅ DELETE route to remove all data from Firebase
@app.delete("/delete-data/")
async def delete_data():
    try:
        ref = db.reference("excel_data")
        ref.delete()  # Deletes all stored data

        return {"message": "All stored data has been deleted successfully"}
    except Exception as e:
        return {"error": f"Failed to delete data: {str(e)}"}

# ✅ Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)