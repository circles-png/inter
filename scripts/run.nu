cd frontend
npm run build
cd ../backend
PROD=1 poetry run hypercorn "src/inter:create_app()" -b 0.0.0.0:5001
