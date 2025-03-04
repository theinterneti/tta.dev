# --- Multi-Stage Build: Builder Stage (for Dependencies) ---
    FROM python:3.11-slim as builder

    # Set the working directory in the container
    WORKDIR /app/build  # Dedicated workdir for builder stage
   
    # Copy only requirements file for caching - IMPORTANT for build speed!
    COPY ../requirements.txt .

    # --- System Dependencies---
    # Install Python dependencies in builder stage
    # Example of installing system packages (uncomment and adjust if needed):
    RUN apt-get update && apt-get install -y python3-pip
    RUN apt-get update && apt-get install -y git
    RUN apt-get update && apt-get install -y sudo
    RUN apt-get update && apt-get install -y curl

    RUN echo "Running pip install in builder stage..."
    RUN pip install --no-cache-dir -r requirements.txt
    RUN echo "pip install finished in builder stage."
    RUN pip list # Let's see what's installed in the builder stage
    
    # --- Final Image: Runtime Stage ---
    FROM python:3.11-slim as final
    
    # Copy application code (after setting workdir)
    COPY ../app
    
    # Copy dependencies from builder stage
    COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
    COPY --from=builder /usr/local/bin /usr/local/bin
    
    # --- System Dependencies (Example - Uncomment and adjust if needed) ---
    # Example of installing system packages (uncomment and adjust if needed):
    # RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev
    
    # --- Expose Ports ---
    # Expose the ports that your application and services will use.
    # 8501:  Likely for Streamlit (if you are using it)
    # 1234:  Default port for LM Studio
    # 7687:  Default Bolt port for Neo4j (though Neo4j should ideally be in a separate container)
    EXPOSE 8501 1234 7687
    
    # --- Create a Non-Root User for Security ---    
    # If you want to run the application as a non-root user, uncomment and adjust the following:
    RUN useradd -m appuser && usermod -aG sudo appuser
    USER appuser
    
    # --- Health Check (Optional but Recommended for Production) ---
    # Uncomment and adjust the command to suit your application's health check endpoint or method.
    # HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD ["python", "/app/src/healthcheck.py"]
    # Example healthcheck.py (you would need to create this):
    # ```python
    # import sys, requests
    # try:
    #     response = requests.get("http://localhost:8501/healthz") # Example Streamlit health endpoint
    #     response.raise_for_status()
    #     print("Service is healthy")
    #     sys.exit(0)
    # except requests.exceptions.RequestException as e:
    #     print(f"Service is unhealthy: {e}")
    #     sys.exit(1)
    # ```
    
    
    # --- Command to Run the Application ---
    # Define the command to execute when the container starts.
    # Adjust the path if your main script is located elsewhere.
    CMD ["python", "src/main.py"]
    
    # --- IMPORTANT REMINDERS ---
    #
    # 1.  .dockerignore FILE (CRITICAL):
    #     - **Ensure you have a `.dockerignore` file** in the same directory as this Dockerfile.
    #     - This file is **essential** to exclude unnecessary files and directories from your Docker image.
    #     - **Example `.dockerignore` contents:**
    #       ```
    #       .git
    #       __pycache__
    #       *.pyc
    #       .env
    #       node_modules/
    #       data/ # Example: exclude your data directory if it shouldn't be in the image
    #       # Add any other files or directories not needed in the production image
    #       ```
    #     - **Without a `.dockerignore`, your image will be unnecessarily large and builds slow.**
    #
    # 2.  ENVIRONMENT VARIABLES:
    #     - **DO NOT hardcode API keys, passwords, or sensitive configuration in the Dockerfile.**
    #     - Pass environment variables at runtime using Docker Compose (`docker-compose.yml`),
    #       `docker run -e`, or your container orchestration system (e.g., Kubernetes).
    #     - Use a `.env` file (and load it in your Python code with `python-dotenv`) for local development ONLY.
    #
    # 3.  PRODUCTION vs. DEVELOPMENT:
    #     - This Dockerfile is optimized for **production** by using a multi-stage build and a non-root user.
    #     - For **development** with VS Code Dev Containers, Docker might mount your source code directly,
    #       making rebuilds faster during development. However, using this Dockerfile for both ensures consistency.
    #
    # 4.  ADJUST `CMD` and `HEALTHCHECK`:
    #     - **Verify that `CMD` correctly points to your main Python application file (`src/main.py` is assumed).**
    #     - **If you implement a health check endpoint, uncomment and adjust the `HEALTHCHECK` instruction.**
    #       Ensure the path in `CMD ["python", "/app/src/healthcheck.py"]` is correct for your health check script.
    #
    # 5.  MULTI-STAGE BUILD BENEFITS:
    #     - **Smaller Final Image:** The final image only contains the runtime dependencies and your application, not build tools.
    #     - **Improved Security:**  Reduces potential attack surface by excluding build tools from the runtime image.
    #     - **Faster Builds (for code changes):** Docker can cache the dependency installation layer in the builder stage, speeding up subsequent builds when only application code changes.