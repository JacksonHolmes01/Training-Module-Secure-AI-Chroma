# Lesson 8: The Gradio Chat UI

## Open the chatbot

Go to **http://localhost:7860** in your browser.

You should see a chat box on the left and a **System status** panel on the right.

1. Click **Refresh /health**. You should see `HTTP 200` and `"chroma_ok":true`
2. Ask: *What is defense in depth?*
3. Wait for the answer. Below it you will see a **Sources** list with a similarity score for each document

---

## Where the API key lives

The UI needs the API key to talk to NGINX. The key is given to the **Gradio server process** as an environment variable:

```yaml
  gradio-ui:
    environment:
      EDGE_API_KEY: "${EDGE_API_KEY}"
```

Your browser talks to Gradio. Gradio's server adds the key and talks to NGINX. **The key never reaches the browser.**

Check this yourself: in your browser, open the developer tools (right-click → **Inspect** → **Network** tab), send a chat message, and click the requests. You will not find `X-API-Key` in anything the browser sends or receives.

If the key were put in browser JavaScript instead, anyone who opened the page could copy it and call the API directly, skipping the UI.

---

## Why the UI goes through NGINX

The UI could connect straight to the API on the internal network. It does not, on purpose:

- the UI gets the **same** checks as every other client: the key, the rate limit, the body size limit
- there is exactly **one** entry point to secure and monitor
- if the UI is ever compromised, it holds only the API key, not Chroma tokens, and it is not even on a network that can reach Chroma

---

## Limits of this UI

This UI has no user login. Anyone who can open `localhost:7860` can chat. That is acceptable only because the port is bound to `127.0.0.1`, so only people using **your** computer can reach it.

Before sharing a UI like this with other people, you would add real user authentication (for example single sign-on) and decide which tenant each user belongs to. That decision would then set `app.tenant`, replacing the fixed `APP_TENANT` value.

Next: [Operations, Testing, and Troubleshooting](09-operations.md)
