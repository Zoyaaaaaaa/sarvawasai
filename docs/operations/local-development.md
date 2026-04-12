# Local Development

## Backend

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Notes

- Keep backend running on `127.0.0.1:8000` for default frontend API calls.
- For environment variables, copy `backend/.env.example` to `backend/.env` and fill secrets.
- Use repository-root `data/` for shared datasets and generated model bundles.
