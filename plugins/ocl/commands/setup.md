---
description: Check that your OCL API token is set up, and walk you through setting it up if not
---

Help the user get their Open Concept Lab (OCL) API token working with the `ocl` plugin. Many users aren't developers, so use plain language and give one step at a time.

The token must never appear in this conversation. Don't ask the user to paste it here or type it after `!`, and never print the token file.

1. Check whether the token file exists and is non-empty, without showing its contents:
   ```bash
   [ -s ~/.config/ocl/token ] && echo "token file found" || echo "no token file"
   ```
2. If it exists, test it:
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Token $(cat ~/.config/ocl/token)" 'https://api.openconceptlab.org/orgs/PIH/sources/PIH/'
   ```
   - `200`: tell the user they're all set, and suggest something to try, e.g. "find PIH concepts named Chest that are in a radiology set".
   - `401` or `403`: the token is wrong or expired. Go to step 3 to replace it.
3. If there's no token or it doesn't work, walk them through it:
   - **Get the token:** sign in at https://app.v3.openconceptlab.org/, open their profile (top right), and copy the **API Token**.
   - **Save it** by running a command in their computer's own terminal app, not in Claude. The command asks for the token without showing it on screen, and saves it where only they can read it.
     - **Mac or Linux:** open the **Terminal** app, paste this, press Enter, then paste the token when asked and press Enter again:
       ```bash
       mkdir -p ~/.config/ocl && read -rsp 'OCL token: ' t && printf %s "$t" > ~/.config/ocl/token && chmod 600 ~/.config/ocl/token; unset t; echo
       ```
     - **Windows:** open **PowerShell** from the Start menu, paste this, press Enter, then paste the token when asked and press Enter again:
       ```powershell
       New-Item -ItemType Directory -Force "$HOME\.config\ocl" | Out-Null; $s = Read-Host 'OCL token' -AsSecureString; [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)) | Set-Content -NoNewline "$HOME\.config\ocl\token"
       ```
   - Ask them to tell you when it's done, then run steps 1 and 2 again to confirm.
