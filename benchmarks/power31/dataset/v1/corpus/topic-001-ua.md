---
type: Resource
title: "Оптимізація Docker через Multi-Stage Build"
description: "Multi-stage build дозволяє зменшити розмір фінального образу Docker. Використову"
timestamp: 2026-01-15T10:00:00
---

# Оптимізація Docker через Multi-Stage Build

Multi-stage build дозволяє зменшити розмір фінального образу Docker. Використовуйте alpine як базовий образ. Копіюйте лише необхідні артефакти з проміжних етапів за допомогою COPY --from.
