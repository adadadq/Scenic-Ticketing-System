## Local Project Skills

These rules apply only inside this Scenic Ticket main project.

- When deploying, redeploying, hotfixing production, checking whether the online project is usable, or answering "can it be deployed now?", first read and follow the local deployment verification skill at `.skills/scenic-deploy-verify/SKILL.md`.
- A deployment is not complete only because files were copied or `systemctl` is active. The deployment verification skill's smoke checks must pass, especially admin login, system settings read/write, ticket read/write, DB health, frontend routing, and clean post-restart logs.
