# Critique of Marcus's Infrastructure Migration Email

## Part 1: Jargon Count (50+ Pieces of Unexplained Jargon)

Marcus's email contains a high density of unexplained acronyms, metrics without context, and engineering terms:

1. **API gateway** (Application Programming Interface gateway)
2. **EOL** (End of Life - software no longer supported)
3. **Kong (2.8.x)** (specific gateway product and version)
4. **NGINX** (web server software)
5. **reverse proxy** (traffic router)
6. **custom Lua plugins** (scripts written in Lua programming language)
7. **rate limiting** (restricting request rates)
8. **JWT validation** (JSON Web Token authentication checks)
9. **mTLS termination** (Mutual Transport Layer Security decryption)
10. **NGINX layer** (specific proxy software stage)
11. **service mesh** (network infrastructure layer)
12. **zero-trust policies** (security paradigm requiring strict identity verification)
13. **east-west** (traffic flow between internal services)
14. **tech debt** (technical debt - cost of future rework caused by easy solutions now)
15. **autoscaling group** (automated server scaling configuration)
16. **gateway nodes** (servers running the gateway software)
17. **fixed ceiling of 24 c5.2xlarge instances** (server count limit and AWS instance type)
18. **12,000 RPS** (Requests Per Second)
19. **p95 < 200ms** (95th percentile response time less than 200 milliseconds)
20. **p99** (99th percentile response time)
21. **checkout service** (application module handling payments)
22. **SLO** (Service Level Objective - target performance metric)
23. **99.95% availability** (target system uptime)
24. **dipped to 99.2%** (actual uptime during incident)
25. **Envoy-based ingress** (routing software)
26. **Kubernetes clusters** (server orchestration system)
27. **proxy and gateway layers** (internal networking tiers)
28. **native service mesh integration** (built-in network control)
29. **Istio sidecars** (helper applications running next to services)
30. **circuit breaking** (stopping requests to a failing service)
31. **retry budgets** (limiting automated retry attempts)
32. **mesh level** (infrastructure network tier)
33. **application code** (software source files)
34. **custom Lua plugins** (repeated scripting reference)
35. **Envoy WASM filters** (WebAssembly modules in Envoy)
36. **CI/CD pipelines** (Continuous Integration / Continuous Deployment automated delivery flows)
37. **deploy Envoy configs via GitOps** (version-controlled deployment practice)
38. **observability stack** (monitoring tools)
39. **StatsD + Grafana setup** (metrics gathering and visualization tools)
40. **OpenTelemetry collectors** (standardized monitoring data collectors)
41. **existing Datadog tenant** (third-party monitoring instance)
42. **blue-green deployment** (running old and new systems in parallel)
43. **synthetic load tests** (simulated traffic tests)
44. **staging** (pre-release testing environment)
45. **cutting over** (switching traffic to the new system)
46. **Istio sidecar injection** (attaching monitoring tools to pods)
47. **pod memory overhead** (memory used by a container)
48. **128MB per pod** (memory quantity)
49. **340 pods** (container count)
50. **42.5 GB of cluster memory** (total memory quantity)
51. **node pool** (group of underlying physical servers)
52. **headroom** (spare capacity)
53. **reserved capacity for autoscaling events** (server capacity set aside for traffic spikes)

---

## Part 2: The Buried Risk

**One-sentence business summary of the buried risk:**
"We are planning to increase our server memory usage by 42.5 GB without verifying if we have enough spare capacity, which could cause our checkout service to run out of memory and crash under heavy Black Friday load, leading to lost sales."

---

## Part 3: The Missing Asks

Instead of a polite dismissal like "Let me know if you have questions," Marcus should be presenting leadership with two specific asks:

1. **Resource/Roadmap Approval Ask:** "We request approval to allocate two platform engineers for eight weeks in Q3. This will delay other Q3 platform roadmap deliverables by two weeks, but it is necessary to secure our gateway before Black Friday."
2. **Budget/Capacity Approval Ask:** "We request approval for a projected $1,200/month increase in our cloud infrastructure budget to cover the additional 42.5 GB of server memory required for the new security architecture."
