# Dockerfile

# existing content

# Add these lines before switching to USER nonroot
RUN chown -R nonroot:nonroot /app && chmod -R 770 /app

# existing content continues...