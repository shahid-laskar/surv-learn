# Secret Rotation Guide

## Kong JWT Secret Rotation
The application relies on a shared JWT secret between FastAPI (which signs the tokens) and Kong (which validates them). To rotate this secret without downtime:

1. **Generate a new secret:**
   Use a secure random string generator.
   ```bash
   openssl rand -hex 32
   ```

2. **Update the Environment Variable:**
   Update the `KONG_JWT_SECRET` in your `.env` file.

3. **Deploy the updated Secret to Kong:**
   You can either restart the `kong-config` container, which runs `setup-kong-jwt.sh` to register the credential, or manually use the Kong Admin API to add the new credential.
   
   To avoid invalidating existing sessions immediately, you can add a second JWT credential to the `sarvanetra-backend` consumer in Kong with the new secret, while keeping the old one. Once you want to invalidate all old sessions, delete the old JWT credential from Kong.

4. **Restart the Application Backend:**
   Restart the `app` container so FastAPI begins signing new tokens with the new secret.
   ```bash
   docker compose restart app
   ```
