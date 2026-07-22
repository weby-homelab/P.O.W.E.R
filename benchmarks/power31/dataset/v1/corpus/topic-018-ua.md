---
type: Resource
title: "Rate Limiting в API Gateway"
description: "Rate limiting обмежує кількість запитів до API. Використовуйте Redis для зберіга"
timestamp: 2026-01-15T10:00:00
---

# Rate Limiting в API Gateway

Rate limiting обмежує кількість запитів до API. Використовуйте Redis для зберігання лічильників. Алгоритм sliding window забезпечує точне обмеження, наприклад 100 запитів за хвилину.
