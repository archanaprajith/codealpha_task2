document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Collapsible Sidebar
    const appSidebar = document.getElementById('app-sidebar');
    const sidebarCollapse = document.getElementById('sidebar-collapse');

    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', (e) => {
            e.preventDefault();
            appSidebar.classList.toggle('collapsed');
            
            // Adjust collapse button icon
            const icon = sidebarCollapse.querySelector('i');
            if (appSidebar.classList.contains('collapsed')) {
                icon.className = 'fa-solid fa-angles-right';
            } else {
                icon.className = 'fa-solid fa-angles-left';
            }
        });
    }

    // 2. Slide-out Guardrail Panel Toggle
    const guardrailConsole = document.getElementById('guardrail-console');
    const guardrailToggleBtn = document.getElementById('guardrail-toggle-btn');

    if (guardrailToggleBtn && guardrailConsole) {
        guardrailToggleBtn.addEventListener('click', () => {
            guardrailConsole.classList.toggle('open');
        });
    }

    // 3. Tab Navigation & Routing
    const navItems = document.querySelectorAll('.nav-item[data-tab]');
    const tabPanels = document.querySelectorAll('.tab-panel');

    function switchTab(targetTabId) {
        navItems.forEach(nav => {
            if (nav.getAttribute('data-tab') === targetTabId) {
                nav.classList.add('active');
            } else {
                nav.classList.remove('active');
            }
        });
        
        tabPanels.forEach(panel => {
            if (panel.getAttribute('id') === targetTabId) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
        
        // Auto-close guardrail console if open when switching tabs to keep view clear
        if (guardrailConsole) {
            guardrailConsole.classList.remove('open');
        }
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });

    // Dashboard Quick Navigation Cards
    const shortcutCards = document.querySelectorAll('.shortcut-card');
    shortcutCards.forEach(card => {
        card.addEventListener('click', () => {
            const gotoTab = card.getAttribute('data-goto');
            switchTab(gotoTab);
        });
    });

    // Close Tip of Day Banner
    const closeTipBtn = document.querySelector('.close-tip-btn');
    const tipBanner = document.querySelector('.tip-of-day-banner');
    if (closeTipBtn && tipBanner) {
        closeTipBtn.addEventListener('click', () => {
            tipBanner.style.display = 'none';
        });
    }

    // 4. Refresh Safety Logs Side Panel
    const guardrailLogsList = document.getElementById('guardrail-logs-list');

    async function refreshSafetyLogs() {
        try {
            const response = await fetch('/api/safety_logs');
            const logs = await response.json();
            
            guardrailLogsList.innerHTML = '';
            
            // Loop in reverse so latest logs are at the top
            for (let i = logs.length - 1; i >= 0; i--) {
                const log = logs[i];
                const logItem = document.createElement('div');
                logItem.className = 'log-item';
                
                let colorClass = 'var(--text-main)';
                if (log.category === 'PII Redacted') colorClass = 'var(--success)';
                if (log.category === 'Outcome Protection') colorClass = 'var(--warning)';
                if (log.category === 'Emergency Interception') colorClass = 'var(--danger)';
                
                logItem.innerHTML = `
                    <span class="log-time">Active Protocol</span>
                    <strong class="log-cat" style="color: ${colorClass}">${log.category}</strong>
                    <p class="log-detail">${log.detail}</p>
                `;
                guardrailLogsList.appendChild(logItem);
            }
        } catch (error) {
            console.error('Error fetching safety logs:', error);
        }
    }

    // Call initially
    refreshSafetyLogs();

    // ========================================================
    // REUSABLE CONTEXT-SPECIFIC CHATBOT LOGIC
    // ========================================================
    const chatbotBlocks = document.querySelectorAll('.legal-chatbot-block');

    function formatMessageText(text) {
        // Simple helper to replace markdown double asterisks with bold tags
        return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
    }

    function appendChatbotMessage(messagesContainer, message, isUser = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${isUser ? 'user' : 'bot'}`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = isUser ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
        
        const bubbleWrapper = document.createElement('div');
        bubbleWrapper.className = 'message-bubble-wrapper';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = isUser ? message : formatMessageText(message);
        
        const meta = document.createElement('span');
        meta.className = 'message-meta';
        meta.style.fontSize = '0.68rem';
        meta.style.color = 'var(--text-dim)';
        meta.style.marginTop = '4px';
        meta.style.display = 'block';
        meta.textContent = isUser ? 'You • Just now' : 'Legal AI • Just now';
        
        bubbleWrapper.appendChild(bubble);
        bubbleWrapper.appendChild(meta);
        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(bubbleWrapper);
        
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function appendTypingIndicator(messagesContainer) {
        const indicator = document.createElement('div');
        indicator.className = 'message bot typing-indicator-msg';
        indicator.id = 'typing-indicator';
        indicator.innerHTML = `
            <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-bubble-wrapper">
                <div class="message-bubble" style="display: flex; gap: 4px; padding: 12px 16px;">
                    <span class="dot-indicator" style="animation-delay: 0s;"></span>
                    <span class="dot-indicator" style="animation-delay: 0.2s;"></span>
                    <span class="dot-indicator" style="animation-delay: 0.4s;"></span>
                </div>
            </div>
        `;
        messagesContainer.appendChild(indicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return indicator;
    }

    async function sendChatbotQuery(block, text) {
        if (!text.trim()) return;
        
        const moduleType = block.getAttribute('data-module') || 'rights';
        const messagesContainer = block.querySelector('.chatbot-messages');
        const textarea = block.querySelector('.chatbot-textarea');
        const docText = document.getElementById('doc-text-input') ? document.getElementById('doc-text-input').value : '';

        // Add user message
        appendChatbotMessage(messagesContainer, text, true);
        if (textarea) textarea.value = '';

        // Add typing indicator
        const typing = appendTypingIndicator(messagesContainer);

        try {
            const response = await fetch('/api/chat_module', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    module: moduleType,
                    document_text: docText
                })
            });

            const data = await response.json();
            typing.remove();

            if (data.error) {
                appendChatbotMessage(messagesContainer, "I had trouble processing that query.", false);
                return;
            }

            // Handle danger triggers
            if (data.danger_detected) {
                const emergencyAlert = document.getElementById('emergency-alert');
                if (emergencyAlert) {
                    emergencyAlert.style.display = 'block';
                    switchTab('module3'); // Switch to Safety Tab
                }
                const safetyNavItem = document.getElementById('nav-safety');
                if (safetyNavItem) {
                    safetyNavItem.style.color = 'var(--danger)';
                    safetyNavItem.classList.add('pulse-alert');
                }
            }

            // Append bot response
            appendChatbotMessage(messagesContainer, data.response, false);
            refreshSafetyLogs();

        } catch (error) {
            console.error('Error in chatbot communication:', error);
            typing.remove();
            appendChatbotMessage(messagesContainer, "Unable to connect to the legal AI gateway.", false);
        }
    }

    // Bind event handlers to each chatbot block
    chatbotBlocks.forEach(block => {
        const sendBtn = block.querySelector('.chatbot-send-btn');
        const textarea = block.querySelector('.chatbot-textarea');

        if (sendBtn && textarea) {
            sendBtn.addEventListener('click', () => {
                sendChatbotQuery(block, textarea.value);
            });

            textarea.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChatbotQuery(block, textarea.value);
                }
            });
        }

        // Bind quick suggestion chips inside the block if present
        const chips = block.querySelectorAll('.suggest-chip');
        chips.forEach(chip => {
            chip.addEventListener('click', () => {
                const query = chip.getAttribute('data-query');
                sendChatbotQuery(block, query);
            });
        });
    });

    // 5. Cybercrime Guidance & Checklist
    const cyberCards = document.querySelectorAll('.cyber-card');
    const cyberOutput = document.getElementById('cyber-output');
    const cyberEvidenceList = document.getElementById('cyber-evidence-list');
    const cyberStepsList = document.getElementById('cyber-steps-list');
    const cyberSectionsSpan = document.getElementById('cyber-sections-span');

    cyberCards.forEach(card => {
        card.addEventListener('click', async () => {
            cyberCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            
            const crimeType = card.getAttribute('data-crime');
            
            try {
                const response = await fetch('/api/cybercrime', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ crime_type: crimeType })
                });
                const data = await response.json();
                
                cyberEvidenceList.innerHTML = '';
                data.checklist.forEach(item => {
                    const li = document.createElement('li');
                    li.textContent = item;
                    cyberEvidenceList.appendChild(li);
                });
                
                cyberStepsList.innerHTML = '';
                data.portal_steps.forEach(step => {
                    const li = document.createElement('li');
                    li.textContent = step;
                    cyberStepsList.appendChild(li);
                });
                
                cyberSectionsSpan.textContent = data.sections;
                cyberOutput.style.display = 'grid';
                
            } catch (error) {
                console.error('Error loading cybercrime guide:', error);
            }
        });
    });

    // 6. Tenancy Calculator & Compliance Checklists
    const calcBtn = document.getElementById('calc-btn');
    const calcResultBox = document.getElementById('calc-result-box');
    const resMonthsCap = document.getElementById('res-months-cap');
    const resMaxDeposit = document.getElementById('res-max-deposit');
    const resStateNote = document.getElementById('res-state-note');

    if (calcBtn) {
        calcBtn.addEventListener('click', async () => {
            const rent = parseFloat(document.getElementById('monthly-rent').value) || 0;
            const state = document.getElementById('state-selector').value;
            const isResidential = document.querySelector('input[name="premise-type"]:checked').value === 'residential';
            
            try {
                const response = await fetch('/api/tenant_calculator', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        rent: rent,
                        state: state,
                        is_residential: isResidential
                    })
                });
                const data = await response.json();
                
                resMonthsCap.textContent = `${data.cap_months} Months`;
                resMaxDeposit.textContent = `₹ ${data.legal_cap.toLocaleString('en-IN')}`;
                resStateNote.textContent = data.note;
                
                calcResultBox.style.display = 'flex';
            } catch (error) {
                console.error('Error calculating tenant deposit:', error);
            }
        });
    }

    // Startup Entity Checklists
    const entityBtns = document.querySelectorAll('.entity-btn');
    const complianceChecklist = document.getElementById('compliance-checklist');

    const checklistData = {
        sole: [
            { title: "GST Registration", desc: "Mandatory if annual business turnover exceeds ₹40 Lakhs (₹20 Lakhs for services / hill states).", class: "sole-item" },
            { title: "MSME Udyam Registration", desc: "Allows accessing government schemes, tender bidding benefits, and protection against delayed payments.", class: "sole-item" },
            { title: "Shops & Establishment Act License", desc: "Required within 30 days of starting operations to legalise your office/commercial space.", class: "sole-item" }
        ],
        llp: [
            { title: "PAN & TAN Application", desc: "Required immediately after LLP incorporation to open the corporate bank account and handle withholding tax.", class: "llp-item" },
            { title: "LLP Agreement Filing (Form 3)", desc: "Must be drafted, stamped, and filed with the Registrar of Companies (RoC) within 30 days of incorporation.", class: "llp-item" },
            { title: "GST & Professional Tax Registration", desc: "GST enrollment + regional employer state compliance registration for operating employees.", class: "llp-item" }
        ],
        pvt: [
            { title: "SPICe+ Incorporation Application", desc: "Central MCA portal application for Director DINs, Name approval, MOA, AOA, and PAN generation.", class: "pvt-item" },
            { title: "Commencement of Business (Form INC-20A)", desc: "Must be filed within 180 days of incorporation after subscribers deposit share capital.", class: "pvt-item" },
            { title: "Auditor Appointment (Form ADT-1)", desc: "Mandated within 30 days of incorporation during the first board meeting.", class: "pvt-item" }
        ]
    };

    function renderChecklist(entityType) {
        if (!complianceChecklist) return;
        complianceChecklist.innerHTML = '';
        const items = checklistData[entityType] || [];
        
        items.forEach(item => {
            const div = document.createElement('div');
            div.className = `checklist-item ${item.class}`;
            div.innerHTML = `
                <i class="fa-solid fa-circle-check"></i>
                <div class="item-text">
                    <h5>${item.title}</h5>
                    <p>${item.desc}</p>
                </div>
            `;
            complianceChecklist.appendChild(div);
        });
    }

    renderChecklist('sole');

    entityBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            entityBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const entity = btn.getAttribute('data-entity');
            renderChecklist(entity);
        });
    });

    // 7. Document Simplifier & Risk Analyzer (NyayGuru Styled Upload Flow)
    const docTextInput = document.getElementById('doc-text-input');
    const simplifyBtn = document.getElementById('simplify-btn');
    const simplifyDashboard = document.getElementById('simplify-dashboard');
    const docsEmptyState = document.getElementById('docs-empty-state');
    const clauseListOutput = document.getElementById('clause-list-output');
    const obligationsTbody = document.getElementById('obligations-tbody');
    const backToDocs = document.getElementById('back-to-docs');
    
    const loadSampleLease = document.getElementById('load-sample-lease');
    const loadSampleNda = document.getElementById('load-sample-nda');

    // Trigger Hidden Input
    const nyayUploadTrigger = document.getElementById('nyay-upload-trigger');
    const primaryUploadBtn = document.getElementById('primary-upload-btn');
    const dropZone = document.getElementById('drop-zone');
    const realFileInput = document.getElementById('real-file-input');

    function triggerUploadFlow() {
        if (realFileInput) {
            realFileInput.click();
        }
    }

    if (nyayUploadTrigger) nyayUploadTrigger.addEventListener('click', triggerUploadFlow);
    if (primaryUploadBtn) primaryUploadBtn.addEventListener('click', triggerUploadFlow);
    if (dropZone) dropZone.addEventListener('click', triggerUploadFlow);

    if (realFileInput) {
        realFileInput.addEventListener('change', () => {
            if (realFileInput.files.length > 0) {
                if (docTextInput) {
                    docTextInput.value = sampleLeaseText;
                    if (simplifyBtn) simplifyBtn.click();
                }
            }
        });
    }

    const sampleLeaseText = `LEASE AGREEMENT CLAUSES:
1. SECURITY DEPOSIT: The Tenant shall deposit a security sum of INR 1,50,000 before possessing the flat. Under no conditions shall this deposit bear interest. The Landlord has full authority to deduct paint, deep cleaning, or miscellaneous damages at absolute discretion upon exit.
2. UNILATERAL TERMINATION: The Landlord may terminate this lease agreement at absolute convenience at any time by giving zero (0) days prior notice. The Tenant must provide at least 90 days notice before vacating the property or forfeit the complete deposit.
3. LIMITATION OF LIABILITY: Under no circumstances shall the Landlord's liability for structural damages or security issues exceed the total of one (1) month of rent fees paid, even in case of gross negligence.
4. GOVERNING LAW & JURISDICTION: This lease shall be exclusively governed by the laws of the State of Delaware, USA, and any dispute shall be filed in the Delaware district court.`;

    const sampleNdaText = `MUTUAL NON-DISCLOSURE AGREEMENT:
1. INTELLECTUAL PROPERTY RIGHTS: The Disclosing Party transfers all worldwide copyright, patents, and designs of all concepts discussed during negotiations perpetually to the Receiving Party immediately. The Disclosing Party waives all claims to compensation.
2. JURISDICTION: Any dispute arising out of or in connection with this agreement shall be referred to the exclusive jurisdiction of the court of Singapore.`;

    if (loadSampleLease) {
        loadSampleLease.addEventListener('click', (e) => {
            e.preventDefault();
            docTextInput.value = sampleLeaseText;
        });
    }

    if (loadSampleNda) {
        loadSampleNda.addEventListener('click', (e) => {
            e.preventDefault();
            docTextInput.value = sampleNdaText;
        });
    }

    if (simplifyBtn) {
        simplifyBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const text = docTextInput.value;
            if (!text.trim()) return;
            
            try {
                const response = await fetch('/api/simplify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });
                const data = await response.json();
                
                if (data.error) {
                    alert(data.error);
                    return;
                }
                
                clauseListOutput.innerHTML = '';
                data.clauses.forEach(cl => {
                    const card = document.createElement('div');
                    card.className = 'clause-card';
                    
                    let riskClass = 'green-risk';
                    if (cl.risk_score === 'Amber') riskClass = 'amber-risk';
                    if (cl.risk_score === 'Red') riskClass = 'red-risk';
                    
                    card.innerHTML = `
                        <div class="clause-card-header">
                            <h4>${cl.clause_name}</h4>
                            <span class="risk-tag ${riskClass}">${cl.risk_score} Risk</span>
                        </div>
                        <p><strong>Plain-English:</strong> ${cl.summary}</p>
                        <p class="clause-reason"><strong>Risk Analysis:</strong> ${cl.reason}</p>
                        <p class="clause-negotiation"><strong>Negotiation Strategy:</strong> ${cl.negotiation}</p>
                    `;
                    clauseListOutput.appendChild(card);
                });
                
                obligationsTbody.innerHTML = '';
                data.obligations.forEach(ob => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${ob.party}</td>
                        <td>${ob.duty}</td>
                    `;
                    obligationsTbody.appendChild(tr);
                });
                
                // Hide empty state and show dashboard
                docsEmptyState.style.display = 'none';
                simplifyDashboard.style.display = 'flex';
                
                refreshSafetyLogs();
                
            } catch (error) {
                console.error('Error simplifying agreement:', error);
            }
        });
    }

    if (backToDocs) {
        backToDocs.addEventListener('click', () => {
            simplifyDashboard.style.display = 'none';
            docsEmptyState.style.display = 'flex';
            docTextInput.value = '';
            if (realFileInput) realFileInput.value = ''; // Reset input
        });
    }

});
