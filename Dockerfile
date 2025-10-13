# Dockerfile

# --- Stage 1: Builder ---
# This stage installs dependencies into a clean environment using a standard Python image.
FROM python:3.9-slim as builder

# Set the working directory
WORKDIR /usr/src/app

# Install dependencies
# Copy only the requirements file to leverage Docker's layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# --- Stage 2: Final Image ---
# This stage builds the final, lean image for production.
FROM python:3.9-slim

# Set the working directory
WORKDIR /usr/src/app

# Copy the installed packages from the builder stage's site-packages
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy the application source code
COPY main.py manager.py models.py./

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using uvicorn.
# The exec form is used to ensure graceful shutdowns.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]