## Matheus Braga

**AI Builder** · Engenharia de Computação na UFG (Goiânia)

Construo com IA soluções para problemas reais e coloco em produção: agentes, automações e sistemas internos,
do primeiro protótipo ao servidor. Portfólio: **[ia.matheusbragadev.com](https://ia.matheusbragadev.com)**

### Agora

- **Grupo Odilon Santos**, Laboratório 3D: sou o único responsável pelo sistema completo do laboratório, do pedido à venda
  (pedidos, produção, catálogo, reposição, precificação e landing page de vendas), com um bot de WhatsApp de 3 agentes de IA
  (n8n + OpenAI + Evolution API) como porta de entrada para as garagens de ônibus.
- **Iniciação Científica na UFG**: extração automática de faturas de água e energia de órgãos públicos para auditoria de consumo.

### Destaques

| Projeto | O que resolve | Resultado |
|---|---|---|
| **Sistema do Laboratório 3D** *(privado, empresa)* | Do pedido à venda: pedidos, fila de produção, catálogo, reposição, precificação com coletor de horas de modelagem e landing page de vendas. Na entrada, um bot de WhatsApp com três agentes (triagem, pedido e ocorrência), memória no Postgres e passagem para um humano. | Feito e validado só por mim; o bot é testado por agentes que simulam funcionários |
| **[FindBus](https://findbus.com.br)** | Mostra em tempo real quais ônibus de Goiânia que estão chegando têm ar-condicionado. Cache em 3 camadas (Redis, Cloudflare, navegador). | 12,6 mil visitas por mês |
| **[Extração de faturas](https://github.com/MatheusBraga1106/extrator-faturas-agua)** | PDF de conta de água → dados estruturados, com OCR para documentos digitalizados e validação cruzada. | Suspeitas de erro de 217 → 63 em 9.820 faturas |
| **Monitor do mercado de confiança** *(privado)* | Geladeira sem atendente do Centro Acadêmico da UFG: câmera e sensores (ESP32-S3) e painel de auditoria. | Em uso desde out/2026 |
| **[Hub Sim Racing](https://github.com/MatheusBraga1106/hub-sim-racing)** | App desktop para equipamentos de simulação, com cena 3D. Feito com subagentes do Claude Code. | 670+ testes, 9 versões publicadas |
| **[3d-web-dev-skills](https://github.com/MatheusBraga1106/3d-web-dev-skills)** | Skill do Claude Code com o padrão de interfaces 3D servidas por Python. | Reutilizada em projetos novos |

### Como eu trabalho com IA

- **Claude Code como equipe:** especificação e plano primeiro, tarefas divididas entre subagentes, revisão a cada entrega.
- **Vários agentes, um projeto:** no estágio, o desenvolvimento é dividido entre 3 agentes do Claude (sistema, WhatsApp e coleta de dados), que se comunicam por contratos de API.
### Stack

- **IA e automação:** n8n · OpenAI · Claude Code · MCP · Gemini · Evolution API · OCR (Tesseract)
- **Dados e backend:** Python · FastAPI · PostgreSQL · Supabase · pandas · SQL · Power BI
- **Infra:** Docker · Dokploy · VPS Linux · Cloudflare
- **Hardware:** ESP32 · Arduino · impressão 3D · Fusion 360

### Contato

[LinkedIn](https://www.linkedin.com/in/mmatheusbraga/) · mmatheusbragamed@gmail.com
