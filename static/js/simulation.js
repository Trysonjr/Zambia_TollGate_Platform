/**
 * Zambia Tollgate Simulation Engine
 * Handles ANPR simulation, RFID sensor scans, fee deduction, mobile money fallback,
 * physical boom barrier software state machine, and audio feedback.
 * 
 * Version 2.0: Null-safe DOM manipulation to prevent crashes across different pages.
 */

// Web Audio API Synthesizer for realistic booth audio feedback
const AudioContextClass = window.AudioContext || window.webkitAudioContext;
let audioCtx = null;

function playTone(freq, type = 'sine', duration = 0.15) {
    try {
        if (!audioCtx) audioCtx = new AudioContextClass();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
    } catch (e) {
        // Audio optional / blocked by browser policy until gesture
    }
}

function playSuccessChime() {
    playTone(523.25, 'sine', 0.12); // C5
    setTimeout(() => playTone(659.25, 'sine', 0.12), 120); // E5
    setTimeout(() => playTone(783.99, 'sine', 0.25), 240); // G5
}

function playWarningTone() {
    playTone(261.63, 'sawtooth', 0.2);
    setTimeout(() => playTone(220.00, 'sawtooth', 0.3), 180);
}

// Global simulation state
let currentVehicleState = null;
let barrierTimer = null;

// ==========================================
// DOM Helper Functions (Null-Safe)
// ==========================================
function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function setHTML(id, value) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = value;
}

function show(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('d-none');
}

function hide(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('d-none');
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const btnArrives = document.getElementById('btnVehicleArrives');
    const btnRfid = document.getElementById('btnScanRfid');
    const btnPayEtag = document.getElementById('btnPayEtag');
    const btnConfirmMomo = document.getElementById('btnConfirmMomo');
    const vehicleTypeSelect = document.getElementById('simVehicleType');
    
    // Auto-update fee display when vehicle type changes
    if (vehicleTypeSelect) {
        vehicleTypeSelect.addEventListener('change', updateFeePreview);
        updateFeePreview();
    }
    
    if (btnArrives) btnArrives.addEventListener('click', simulateVehicleArrival);
    if (btnRfid) btnRfid.addEventListener('click', simulateRfidScan);
    if (btnPayEtag) btnPayEtag.addEventListener('click', () => processTollPayment('Toll Account / E-Tag'));
    
    const btnPayEtagLeft = document.getElementById('btnPayEtagLeft');
    if (btnPayEtagLeft) btnPayEtagLeft.addEventListener('click', () => processTollPayment('Toll Account / E-Tag'));
    
    if (btnConfirmMomo) btnConfirmMomo.addEventListener('click', handleMomoPaymentConfirm);
});

// Update preview fee in UI based on selected classification
function updateFeePreview() {
    const vehicleTypeSelect = document.getElementById('simVehicleType');
    const feePreview = document.getElementById('feePreviewBadge');
    if (!vehicleTypeSelect || !feePreview) return;
    
    const feeMap = {
        'Light Vehicle': 20.00,
        'Medium Vehicle': 50.00,
        'Heavy Vehicle': 100.00,
        'Abnormal Load': 250.00
    };
    const fee = feeMap[vehicleTypeSelect.value] || 20.00;
    feePreview.textContent = `K${fee.toFixed(2)}`;
}

// Quick fill preset helper for presentations
function setDemoPreset(plate, type, tollgateId = 1) {
    const simPlate = document.getElementById('simPlate');
    const simType = document.getElementById('simVehicleType');
    const simGate = document.getElementById('simTollgate');
    const simFormCard = document.getElementById('simFormCard');
    
    if (simPlate) simPlate.value = plate;
    if (simType) simType.value = type;
    if (simGate) simGate.value = tollgateId;
    
    updateFeePreview();
    
    if (simFormCard) {
        simFormCard.scrollIntoView({ behavior: 'smooth' });
    }
}

// 1. Vehicle Arrival & ANPR Simulation
async function simulateVehicleArrival() {
    const plateInput = document.getElementById('simPlate');
    const plate = plateInput?.value.trim().toUpperCase();
    const vehicleType = document.getElementById('simVehicleType')?.value || 'Light Vehicle';
    const tollgateId = document.getElementById('simTollgate')?.value || 1;
    const laneNumber = document.getElementById('simLane')?.value || 1;
    
    if (!plate) {
        alert('Please enter or select a vehicle registration plate.');
        if (plateInput) plateInput.focus();
        return;
    }
    
    // Visual scan animation
    const scanZone = document.getElementById('anprScanZone');
    scanZone?.classList.add('scanning');
    playTone(880, 'sine', 0.1);
    
    // Reset payment / alert boxes
    hide('paymentAlertBox');
    hide('etagActionBox');
    hide('momoActionBox');
    
    try {
        const response = await fetch('/api/simulation/detect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                registration_number: plate,
                vehicle_type: vehicleType,
                tollgate_id: tollgateId,
                lane_number: laneNumber
            })
        });
        
        const data = await response.json();
        currentVehicleState = data;
        
        setTimeout(() => {
            scanZone?.classList.remove('scanning');
            renderDetectionResults(data);
        }, 700); // realistic optical delay
        
    } catch (err) {
        scanZone?.classList.remove('scanning');
        console.error('Detection failed:', err);
    }
}

// Render detection output in the cockpit
function renderDetectionResults(data) {
    show('detectedVehicleSection');
    
    // Update visual graphic display
    setText('graphicPlate', data.registration_number);
    setText('graphicType', data.vehicle_type);
    
    // Update telemetry table
    setHTML('resStatus', '<span class="badge bg-success"><i class="fa fa-check-circle me-1"></i>Vehicle Detected</span>');
    setText('resPlate', data.registration_number);
    setText('resType', data.vehicle_type);
    setText('resTimestamp', data.timestamp);
    setText('resConfidence', data.anpr_confidence);
    setText('resFee', `K${parseFloat(data.toll_fee).toFixed(2)}`);
    
    // Account details
    setText('resOwner', data.owner_name || '—');
    setText('resAccount', data.account_number || '—');
    setText('resRfid', data.rfid_tag || '—');
    setText('resBalance', `K${parseFloat(data.balance).toFixed(2)}`);
    
    const balanceElem = document.getElementById('resBalance');
    if (balanceElem) {
        balanceElem.className = data.has_sufficient_balance
            ? 'fw-bold text-success'
            : 'fw-bold text-danger';
    }
    
    // Enable simulated RFID scan button
    const scanBtn = document.getElementById('btnScanRfid');
    if (scanBtn) scanBtn.disabled = false;
    
    // Decision logic for payment controls
    evaluatePaymentOptions(data);
}

// 2. Simulated RFID / E-Tag Scan
async function simulateRfidScan() {
    if (!currentVehicleState) return;
    
    playTone(950, 'square', 0.15);
    const rfidBadge = document.getElementById('rfidScanBadge');
    if (!rfidBadge) return;
    
    rfidBadge.classList.remove('d-none');
    rfidBadge.innerHTML = `<i class="fa fa-spinner fa-spin me-1"></i> Interrogating E-Tag (${currentVehicleState.rfid_tag})...`;
    
    try {
        const response = await fetch('/api/simulation/rfid-scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rfid_tag: currentVehicleState.rfid_tag,
                registration_number: currentVehicleState.registration_number,
                vehicle_type: currentVehicleState.vehicle_type
            })
        });
        
        const data = await response.json();
        setTimeout(() => {
            if (data.success) {
                rfidBadge.className = 'rfid-pulse-badge mb-3';
                rfidBadge.innerHTML = `<i class="fa fa-rss me-1"></i> E-Tag Verified: <strong>${data.rfid_tag}</strong> | Balance: <strong>K${parseFloat(data.balance).toFixed(2)}</strong>`;
            } else {
                rfidBadge.className = 'badge bg-danger p-2 mb-3';
                rfidBadge.innerHTML = `<i class="fa fa-exclamation-circle me-1"></i> ${data.message}`;
            }
        }, 500);
        
    } catch (e) {
        console.error(e);
    }
}

// 3. Payment Option Evaluator
function evaluatePaymentOptions(data) {
    const etagBox        = document.getElementById('etagActionBox');
    const momoBox        = document.getElementById('momoActionBox');
    const leftPaymentBox = document.getElementById('leftPaymentActionBox');
    const leftEtagBox    = document.getElementById('leftEtagBox');
    const leftMomoBox    = document.getElementById('leftMomoBox');

    // Always reveal the left payment box when a vehicle is detected
    leftPaymentBox?.classList.remove('d-none');

    const btnPayEtag     = document.getElementById('btnPayEtag');
    const btnPayEtagLeft = document.getElementById('btnPayEtagLeft');

    if (data.is_registered) {
        etagBox?.classList.remove('d-none');
        leftEtagBox?.classList.remove('d-none');

        if (data.has_sufficient_balance) {
            const buttonHtml = `<i class="fa fa-bolt me-2"></i>Verify & Deduct Toll Fee (E-Tag) — K${parseFloat(data.toll_fee).toFixed(2)}`;
            
            if (btnPayEtag) {
                btnPayEtag.className = 'btn btn-success btn-lg w-100 fw-bold shadow-sm';
                btnPayEtag.innerHTML = buttonHtml;
            }
            if (btnPayEtagLeft) {
                btnPayEtagLeft.className = 'btn btn-success btn-lg w-100 fw-bold shadow border-2 border-white';
                btnPayEtagLeft.innerHTML = buttonHtml;
            }
            momoBox?.classList.add('d-none');
            leftMomoBox?.classList.add('d-none');
        } else {
            // Insufficient balance
            const disabledHtml = `<i class="fa fa-times-circle me-2"></i>Insufficient E-Tag Balance (Available: K${parseFloat(data.balance).toFixed(2)})`;
            if (btnPayEtag) {
                btnPayEtag.className = 'btn btn-outline-secondary w-100 disabled';
                btnPayEtag.innerHTML = disabledHtml;
            }
            if (btnPayEtagLeft) {
                btnPayEtagLeft.className = 'btn btn-outline-secondary w-100 disabled';
                btnPayEtagLeft.innerHTML = disabledHtml;
            }
            
            // Show Mobile Money alternative on both panels
            momoBox?.classList.remove('d-none');
            leftMomoBox?.classList.remove('d-none');
            showPaymentAlert(`Insufficient Balance! Toll fee is K${parseFloat(data.toll_fee).toFixed(2)}, but account balance is K${parseFloat(data.balance).toFixed(2)}. Please pay using Mobile Money.`, 'warning');
            playWarningTone();
        }
    } else {
        // Unregistered vehicle
        etagBox?.classList.add('d-none');
        leftEtagBox?.classList.add('d-none');
        momoBox?.classList.remove('d-none');
        leftMomoBox?.classList.remove('d-none');
        showPaymentAlert(`Unregistered Vehicle (${data.registration_number})! No electronic toll account linked. Please use Mobile Money.`, 'info');
    }
}

// 4. Payment Execution
async function processTollPayment(method) {
    if (!currentVehicleState) return;
    
    const tollgateId = document.getElementById('simTollgate')?.value || 1;
    const laneNumber = document.getElementById('simLane')?.value || 1;
    
    const payload = {
        registration_number: currentVehicleState.registration_number,
        vehicle_type: currentVehicleState.vehicle_type,
        tollgate_id: tollgateId,
        lane_number: laneNumber,
        payment_method: method
    };
    
    try {
        const response = await fetch('/api/simulation/process-payment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const res = await response.json();
        
        if (res.success) {
            playSuccessChime();
            showPaymentAlert(`<strong>Payment Successful!</strong> Reference: ${res.transaction_ref}. Toll Fee: K${parseFloat(res.fee).toFixed(2)} paid via ${res.payment_method}.`, 'success');
            
            // Mark both buttons as paid
            const btnPayEtag = document.getElementById('btnPayEtag');
            const btnPayEtagLeft = document.getElementById('btnPayEtagLeft');
            
            if (btnPayEtag) {
                btnPayEtag.className = 'btn btn-secondary btn-lg w-100 disabled';
                btnPayEtag.innerHTML = '<i class="fa fa-check-circle me-2"></i>Toll Paid (Cleared)';
            }
            if (btnPayEtagLeft) {
                btnPayEtagLeft.className = 'btn btn-secondary btn-lg w-100 disabled';
                btnPayEtagLeft.innerHTML = '<i class="fa fa-check-circle me-2"></i>Toll Paid (Cleared)';
            }
            
            // If balance deduction happened, update display
            if (res.balance_after !== null && res.balance_after !== undefined) {
                setText('resBalance', `K${parseFloat(res.balance_after).toFixed(2)}`);
            }
            
            // Trigger Automated Physical Barrier Simulation
            triggerBarrierOpen();
            
            // Append to recent transactions ledger in live page
            appendLiveTransactionRow(res);
            
        } else {
            playWarningTone();
            showPaymentAlert(`<strong>Payment Rejected:</strong> ${res.message}`, 'danger');
            if (res.can_use_mobile_money) {
                show('momoActionBox');
            }
        }
    } catch (e) {
        console.error('Payment failed:', e);
        showPaymentAlert('Payment communication error. Please retry.', 'danger');
    }
}

// 5. Mobile Money Modal Handler
function handleMomoPaymentConfirm() {
    const provider = document.getElementById('momoProvider')?.value || 'MTN Mobile Money';
    const modalEl = document.getElementById('momoPaymentModal');
    const modal = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;
    if (modal) modal.hide();
    
    processTollPayment(provider);
}

// 6. Automated Barrier Simulation
function triggerBarrierOpen() {
    const barrierArm = document.getElementById('barrierArm');
    const lightRed = document.getElementById('lightRed');
    const lightGreen = document.getElementById('lightGreen');
    const barrierStatusBadge = document.getElementById('barrierStatusBadge');
    const barrierStatusText = document.getElementById('barrierStatusText');
    const countdownBadge = document.getElementById('barrierCountdown');
    
    // Status changes: CLOSED -> OPEN
    barrierArm?.classList.add('open');
    lightRed?.classList.remove('active');
    lightGreen?.classList.add('active');
    
    if (barrierStatusBadge) {
        barrierStatusBadge.className = 'badge badge-open fs-6';
        barrierStatusBadge.textContent = 'OPEN';
    }
    if (barrierStatusText) {
        barrierStatusText.textContent = 'Payment verified — Barrier Opening';
    }
    countdownBadge?.classList.remove('d-none');
    
    // Notify server of barrier opening
    fetch('/api/simulation/barrier-trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            state: 'OPEN', 
            lane_number: document.getElementById('simLane')?.value || 1 
        })
    });
    
    // Countdown timer: 4 seconds before resetting OPEN -> CLOSED
    let secondsLeft = 4;
    if (countdownBadge) countdownBadge.textContent = `Auto-closing in ${secondsLeft}s`;
    
    if (barrierTimer) clearInterval(barrierTimer);
    
    barrierTimer = setInterval(() => {
        secondsLeft--;
        if (secondsLeft > 0) {
            if (countdownBadge) countdownBadge.textContent = `Auto-closing in ${secondsLeft}s`;
        } else {
            clearInterval(barrierTimer);
            
            // OPEN -> CLOSED
            barrierArm?.classList.remove('open');
            lightGreen?.classList.remove('active');
            lightRed?.classList.add('active');
            
            if (barrierStatusBadge) {
                barrierStatusBadge.className = 'badge badge-closed fs-6';
                barrierStatusBadge.textContent = 'CLOSED';
            }
            if (barrierStatusText) {
                barrierStatusText.textContent = 'Vehicle Cleared — Barrier Closed';
            }
            countdownBadge?.classList.add('d-none');
            
            // Notify server of barrier close
            fetch('/api/simulation/barrier-trigger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    state: 'CLOSED', 
                    lane_number: document.getElementById('simLane')?.value || 1 
                })
            });
        }
    }, 1000);
}

function showPaymentAlert(msg, type = 'info') {
    const box = document.getElementById('paymentAlertBox');
    if (!box) return;
    
    box.className = `alert alert-${type} shadow-sm`;
    box.innerHTML = `<i class="fa fa-info-circle me-1"></i> ${msg}`;
    box.classList.remove('d-none');
}

function appendLiveTransactionRow(tx) {
    const tbody = document.getElementById('recentTxnBody');
    if (!tbody) return;
    
    const tr = document.createElement('tr');
    tr.className = 'table-success';
    tr.innerHTML = `
        <td><span class="badge bg-secondary font-monospace">${tx.transaction_ref}</span></td>
        <td class="fw-bold">${tx.vehicle_reg}</td>
        <td>${tx.tollgate_name || 'Lusaka East'} (${tx.lane_number})</td>
        <td class="fw-bold text-success">K${parseFloat(tx.fee).toFixed(2)}</td>
        <td><span class="badge bg-primary">${tx.payment_method}</span></td>
        <td><span class="badge bg-success">SUCCESSFUL</span></td>
        <td>Just now</td>
    `;
    tbody.insertBefore(tr, tbody.firstChild);
}