# Stakeholder Memo: Upgrading Our Traffic Routing Infrastructure to Secure Black Friday Operations

**To:** Sarah (VP of Engineering), David (Head of Product)  
**From:** Marcus (Platform Engineering Lead)  
**Date:** June 12, 2026  
**Subject:** Infrastructure Upgrade to Prevent Checkout Slowdowns for Black Friday  

### Overview
We are initiating an upgrade of our core website traffic routing system. This upgrade is critical to ensure our checkout service remains online and stable under heavy user traffic, and it must be completed before our upcoming Black Friday peak traffic window. The total project timeline is eight weeks, requiring the dedication of two platform engineers.

### Context: Last Year's Outage
During last year's Black Friday peak, our traffic routing system reached its capacity limit. This led to checkout service degradation and 47 minutes of service slowdowns, directly impacting customer transactions and revenue. The system we currently use is outdated and no longer receives security updates, making it a reliability and security risk for this year's event.

### Proposed Solution
We plan to replace our traffic routing system with a modern, more reliable one. This upgrade will natively support our internal security policies, handle larger traffic spikes, and improve system observability. Implementing this change requires updating several of our internal helper tools, which represents the bulk of the eight-week timeline. 

### Key Risk: Server Capacity
The primary risk is that the new system will require more server memory resources than we currently have allocated. If the new system runs out of memory under peak traffic, we could experience the same checkout slowdowns and outages we saw last Black Friday. To mitigate this risk, we must perform simulated high-traffic load tests to validate our capacity needs by September 15.

### Required Actions & Decisions
We need the following approvals and decisions to proceed:
1. **Resource Approval:** Approval to dedicate 2 engineers from the platform team for 8 weeks. This will delay other planned platform team features by 2 weeks.
2. **Roadmap Alignment:** Confirmation from David that pausing feature development for these 2 engineers for 8 weeks does not conflict with urgent product launch commitments.
3. **Load Testing Schedule:** A decision on whether we should run the simulated traffic test during normal business hours or off-hours (off-hours testing is safer but requires additional after-hours staffing).
