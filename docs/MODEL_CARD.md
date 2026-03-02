# Model Card: AI Discovery Workshop Facilitator

**Model Name:** AI Discovery Workshop Facilitator (Aida)
**Model Version:** 1.0
**Last Updated:** November 19, 2024
**Model Type:** Multi-Agent Conversational AI System
**Status:** Production

---

## Model Details

### Overview
The AI Discovery Workshop Facilitator (Aida) is a multi-agent conversational AI system designed to guide facilitators and participants through AI Discovery Workshops. It combines multiple Azure OpenAI models with specialized personas and grounding documents to provide expert guidance across different aspects of workshop facilitation.

### Model Architecture

**Agent Composition:**

| Agent | Base Model | Temperature | Purpose |
|-------|------------|-------------|----------|
| Multi-Agent Router | gpt-4.1-nano | 0.5 | Route conversations to appropriate expert |
| Facilitator | gpt-5.1-chat | 1.0 | Primary workshop facilitation guidance |
| Design Thinking Expert | o4-mini | 1.0 | Specialized design thinking methodologies |
| Document Generator | o4-mini | 1.0 | Workshop documentation and report generation |
| Customer Personas | gpt-5.1-chat | 0.5 | Industry-specific role-playing agents |
| Title Generator | gpt-4 | 0.3 | Auto-generate conversation titles |

**Framework Stack:**
- **Orchestration:** LangGraph for agent workflows
- **LLM Integration:** LangChain with Azure OpenAI
- **UI Framework:** Chainlit for conversational interface
- **Infrastructure:** Azure App Service, Azure OpenAI, Azure Storage

### Intended Use

**Primary Use Cases:**
1. **Workshop Facilitation:** Guide facilitators through the 12-step AI Discovery Workshop process
2. **Methodology Guidance:** Provide design thinking and ideation techniques
3. **Documentation:** Generate workshop reports and summaries
4. **Training:** Help facilitators learn workshop methodologies
5. **Practice Scenarios:** Role-play with customer personas for training

**Intended Users:**
- Workshop facilitators (professional services consultants)
- AI program managers
- Innovation teams
- Business analysts
- Training participants

**Deployment Context:**
- Internal enterprise tool for Microsoft and partners
- Workshop training environments
- Real-world client workshops (with human facilitator present)

### Out-of-Scope Uses

**The system should NOT be used for:**

❌ **Autonomous Decision-Making:** System cannot make business decisions without human oversight
❌ **Legal/Compliance Advice:** Not qualified to provide legal or regulatory guidance
❌ **Medical/Health Advice:** No medical or health-related recommendations
❌ **Financial Advice:** Cannot provide investment or financial planning guidance
❌ **Security-Critical Operations:** Not suitable for security-sensitive decision-making
❌ **Production Code Generation:** Generated code is for educational purposes only
❌ **Unattended Operation:** Requires human facilitator oversight
❌ **Children/Minors:** Not designed or evaluated for use by minors

---

## Training Data

### Base Models
The system uses pre-trained Azure OpenAI models:
- **GPT-4o:** Trained on diverse internet text (cutoff varies by model version)
- **GPT-4.1-nano:** Optimized lightweight model for routing decisions
- **o4-mini:** Reasoning-optimized model for complex tasks

**Training Data Characteristics:**
- Primarily English language
- Broad internet corpus including books, websites, academic papers
- Data cutoff dates vary by model (check Azure OpenAI documentation)
- No proprietary workshop data used in base model training

### Grounding Documents

The system enhances base models with workshop-specific grounding documents:

| Document Type | Content | Update Frequency |
|---------------|---------|------------------|
| Facilitator Persona | Workshop methodology, facilitation techniques | Quarterly |
| Design Thinking Guide | Brainstorming, journey mapping, ideation methods | Semi-annually |
| Industry Personas | Banking, healthcare, construction use cases | As needed |
| Guardrails | Safety rules, formatting guidelines | As needed |

**Document Characteristics:**
- Curated by Microsoft workshop experts
- Reviewed for accuracy and bias
- Version controlled in repository
- English language only (currently)

**Known Limitations of Training Data:**
- Base models may reflect biases in internet text
- Workshop methodologies reflect Microsoft's approach (not universal)
- Limited representation of non-English speaking regions
- Industry personas based on common scenarios (may not fit all contexts)

---

## Evaluation & Performance

### Evaluation Methodology

**Pre-Deployment Testing:**
1. **Functionality Testing:** Validate 12-step workshop flow completion
2. **Response Quality:** Human review of 100+ sample interactions
3. **Persona Consistency:** Verify agents maintain appropriate roles
4. **Safety Testing:** Red team exercises for prompt injection, harmful content

**Ongoing Monitoring:**
- User feedback ratings (thumbs up/down)
- Workshop facilitator surveys
- Escalation rate tracking
- Response time and availability metrics

### Performance Metrics

**Current Performance (as of last evaluation):**

| Metric | Target | Current |
|--------|--------|---------|
| System Availability | >99% | 99.5% |
| Average Response Time | <3 seconds | 2.1 seconds |
| User Satisfaction (workshops) | >80% | 85% |
| Escalation Rate | <5% | 3.2% |
| Prompt Adherence | >95% | 97% |

**Quality Metrics:**
- **Relevance:** ~90% of responses rated relevant by facilitators
- **Accuracy:** No known factual errors in workshop methodology
- **Consistency:** Persona adherence >95% across conversations
- **Completeness:** Successfully guides through all 12 workshop steps

### Known Failure Modes

**Hallucination Risk:**
- **Severity:** Medium
- **Description:** May generate plausible but incorrect workshop details
- **Mitigation:** Emphasize verification with facilitator guides, human oversight required
- **Example:** Inventing specific company policies or statistics

**Context Limitations:**
- **Severity:** Medium
- **Description:** Cannot access company-specific information or systems
- **Mitigation:** Clear disclosure, remind users to provide context
- **Example:** Cannot reference internal company processes not described in conversation

**Repetition/Loops:**
- **Severity:** Low
- **Description:** May repeat similar suggestions if user doesn't progress
- **Mitigation:** Escalation mechanism triggers after extended conversations
- **Example:** Repeatedly suggesting same design thinking technique

**Off-Topic Responses:**
- **Severity:** Low
- **Description:** Occasionally provides tangential information
- **Mitigation:** Guardrails emphasize staying on workshop topics
- **Example:** Providing general AI information instead of workshop-specific guidance

**Bias Manifestation:**
- **Severity:** Low-Medium
- **Description:** May reflect industry stereotypes from training data
- **Mitigation:** Regular fairness audits, diverse persona testing
- **Example:** Assuming larger companies have more AI readiness

---

## Ethical Considerations

### Fairness & Bias

**Identified Bias Risks:**
1. **Language Bias:** English-only system excludes non-English speakers
2. **Industry Bias:** Pre-defined personas may not represent all industries
3. **Cultural Bias:** Workshop methodology reflects Western business practices
4. **Technical Bias:** Assumes users have baseline AI/technology knowledge

**Mitigation Strategies:**
- Regular fairness audits across industry types
- Diverse testing with different user personas
- Plans for multi-language support (future)
- Beginner-friendly mode with simplified explanations

**Fairness Evaluation Results:**
- Industry coverage: 5 major sectors represented
- Company size: No significant bias detected between small/large organizations
- Experience level: Adapts well to beginner vs. expert queries
- Regional representation: Limited (primarily Western business contexts)

### Privacy & Data Protection

**Data Collection:**
- User conversation history (for session continuity)
- Interaction metadata (timestamps, agent selections)
- Feedback ratings (thumbs up/down)

**Data Usage:**
- Stored in encrypted Azure Blob Storage
- Used only for improving user experience and system monitoring
- NOT used for training Azure OpenAI models (per Azure guarantee)
- Automatically deleted after 90 days of inactivity

**Privacy Controls:**
- Per-user conversation isolation (no cross-user access)
- No PII required to use system (username/email only for auth)
- Data export available on request
- Data deletion available on request

**Privacy Risks:**
- Users may inadvertently share sensitive business information in conversations
- Conversation history persisted for 90 days
- Administrators have access to conversation logs (for support purposes)

**Mitigations:**
- Clear privacy notice on first use
- Warning not to share confidential information
- PII detection alerts (planned enhancement)
- Audit logging of admin access

### Transparency

**User Disclosure:**
- ✅ Clear "AI Assistant" labeling in interface
- ✅ Disclosure of AI-generated content
- ✅ Links to documentation and support
- ⏳ Model version information (planned)
- ⏳ Confidence indicators (planned)

**Explainability:**
- Agent routing decisions logged (admin view only)
- Conversation history available to users
- Limited: No per-response confidence scores
- Limited: No explanation of why specific guidance provided

### Safety & Security

**Safety Measures:**
- System prompt protection against injection
- Input validation for malicious patterns
- Guardrails against off-topic requests
- Rate limiting (planned)
- Content safety filtering (planned enhancement)

**Security Controls:**
- Managed identity authentication (no stored secrets)
- HTTPS/TLS encryption in transit
- Azure Storage encryption at rest
- Private endpoints for Azure services
- Regular security scanning (Bandit, CodeQL, Checkov)

**Abuse Prevention:**
- User authentication required
- Session isolation prevents cross-user attacks
- Abuse monitoring (planned enhancement)
- Escalation mechanism for concerning conversations

---

## Limitations

### Technical Limitations

1. **No Real-Time External Data:**
   - Cannot access internet, company systems, or real-time information
   - Knowledge limited to training data cutoff dates
   - Cannot verify current company policies or data

2. **Context Window Constraints:**
   - Limited conversation history length (~8K-128K tokens depending on model)
   - Very long workshops may lose early context
   - Mitigation: Summarization and key point extraction

3. **Language Support:**
   - English only (currently)
   - No multi-language conversation support
   - May struggle with non-English company/product names

4. **Multimodal Limitations:**
   - Text-only input/output (currently)
   - Cannot analyze uploaded images, diagrams, or documents
   - Mermaid diagrams for visualization only

5. **Determinism:**
   - Responses may vary between identical queries (by design)
   - Temperature settings balance creativity vs. consistency
   - Not suitable for tasks requiring exact reproducibility

### Knowledge Limitations

1. **Temporal Limitations:**
   - Training data has cutoff dates (varies by model)
   - Cannot provide information on recent events
   - Workshop methodologies may evolve faster than updates

2. **Domain Specificity:**
   - Deep expertise in workshop facilitation only
   - Limited knowledge of specific industries' technical details
   - Cannot replace subject matter experts in specialized domains

3. **Company Context:**
   - No access to specific company data, processes, or culture
   - Provides general guidance that may need customization
   - Cannot validate company-specific feasibility

### Operational Limitations

1. **Requires Human Oversight:**
   - Not designed for autonomous operation
   - Facilitator must validate suggestions
   - Cannot handle crisis situations or conflicts

2. **Scalability:**
   - Concurrent user limit based on Azure OpenAI quota
   - Response time may degrade under high load
   - Cost scales with usage (token consumption)

3. **Availability:**
   - Dependent on Azure service uptime
   - No offline mode available
   - Internet connectivity required

---

## Recommendations for Use

### Best Practices

**For Facilitators:**
1. ✅ **Use as a Guide, Not Authority:** Verify all suggestions against your expertise
2. ✅ **Provide Context:** Share relevant workshop details for better guidance
3. ✅ **Stay Engaged:** Monitor AI responses and intervene if needed
4. ✅ **Verify Facts:** Check any statistics or claims against authoritative sources
5. ✅ **Adapt Suggestions:** Customize AI guidance to your specific context

**For Participants:**
1. ✅ **Ask Clarifying Questions:** AI can explain concepts in different ways
2. ✅ **Provide Feedback:** Use thumbs up/down to improve responses
3. ✅ **Stay on Topic:** Best results when focused on workshop objectives
4. ✅ **Don't Share Sensitive Info:** Avoid PII, confidential business data
5. ✅ **Escalate When Needed:** Request human facilitator for complex issues

### When to Seek Human Help

**Immediate Escalation Required:**
- Legal or compliance questions
- Sensitive personnel issues
- Conflicts between participants
- Ethical dilemmas or controversial topics
- Security or privacy concerns
- Health and safety matters

**Consider Human Expertise:**
- Highly company-specific scenarios
- Complex technical architecture decisions
- Strategic business planning
- Budget and resource allocation
- Stakeholder management challenges
- Crisis or urgent situations

**System Escalation Triggers:**
- AI expresses uncertainty or low confidence
- Repetitive or circular conversations
- User frustration indicators detected
- Content safety filter activated
- Conversation exceeds 20+ exchanges without resolution

---

## Maintenance & Updates

### Update Schedule

**Model Versions:**
- Base models managed by Azure OpenAI (automatic updates)
- Monitor Azure OpenAI announcements for version changes
- Test new model versions in staging before production

**Grounding Documents:**
- **Quarterly Review:** Workshop methodology updates
- **Semi-Annual Review:** Persona and use case refreshes
- **As-Needed:** Urgent corrections or new workshop formats

**System Code:**
- **Monthly:** Dependency updates and security patches
- **Quarterly:** Feature enhancements and RAI improvements
- **Continuous:** Bug fixes and critical security updates

### Monitoring & Maintenance

**Continuous Monitoring:**
- System availability and performance metrics
- User satisfaction ratings
- Error rates and escalation triggers
- Safety and abuse indicators

**Periodic Reviews:**
- **Weekly:** Safety metrics dashboard
- **Monthly:** User feedback analysis
- **Quarterly:** Full RAI evaluation and fairness audit
- **Annually:** Comprehensive model card review

### Versioning

**Version History:**

| Version | Date | Changes | Impact |
|---------|------|---------|--------|
| 1.0 | 2024-11-19 | Initial production release | - |

**Breaking Change Policy:**
- Major changes require RAI re-review
- User-facing changes communicated 2 weeks in advance
- Backward compatibility maintained when possible
- Rollback plan required for all updates

---

## Contact & Feedback

### Reporting Issues

**Security Vulnerabilities:**
- **DO NOT** report via public issues
- Email: [SECURITY.md](../SECURITY.md)
- Microsoft Security Response Center

**RAI Concerns:**
- Bias or fairness issues
- Safety or ethical concerns
- Privacy violations
- Email: rai-concerns@your-org.com

**Product Feedback:**
- Feature requests
- Usability issues
- General suggestions
- GitHub Issues: [repo URL]

### Support Channels

**Technical Support:**
- Documentation: [docs/]
- Email: support@your-org.com
- Internal Teams channel (for Microsoft)

**Training Resources:**
- Workshop facilitator training
- AI Discovery methodology guide
- Best practices documentation

---

## Glossary

**Agent:** A specialized AI component with a specific persona and purpose (e.g., Facilitator, Design Thinking Expert)

**Grounding Document:** Reference material provided to AI to enhance accuracy and relevance

**Hallucination:** When AI generates plausible but incorrect information not supported by training data

**Persona:** The role, tone, and expertise profile an agent adopts

**Prompt Injection:** Malicious attempt to override AI system instructions

**RAI:** Responsible AI - principles and practices for ethical AI development and deployment

**Temperature:** Parameter controlling randomness in AI responses (0 = deterministic, 2 = creative)

---

## References

### Microsoft RAI Resources
- [Microsoft Responsible AI Principles](https://www.microsoft.com/ai/responsible-ai)
- [Azure OpenAI Responsible AI Documentation](https://learn.microsoft.com/azure/ai-services/openai/concepts/safety)
- [Microsoft AI Fairness Checklist](https://www.microsoft.com/en-us/research/project/ai-fairness-checklist/)

### Technical Documentation
- [Azure OpenAI Service Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Chainlit Documentation](https://docs.chainlit.io/)

### Related Documents
- [RAI Review](RAI_REVIEW.md) - Comprehensive responsible AI assessment
- [Security Documentation](security/README.md) - Security controls and practices
- [STRIDE Threat Model](security/STRIDE_THREAT_MODEL.md) - Security threat analysis
- [Architecture Documentation](../ARCHITECTURE.md) - System design and infrastructure

---

**Model Card Version:** 1.0
**Last Updated:** November 19, 2024
**Next Review:** February 19, 2025
**Owner:** Engineering Team + RAI Review Board

---

*This model card follows the format recommended by [Mitchell et al., 2019](https://arxiv.org/abs/1810.03993) and [Microsoft's Model Card guidance](https://www.microsoft.com/en-us/research/project/datasheets-for-datasets/).*
