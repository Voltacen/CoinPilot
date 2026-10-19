document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("transfer-modal");
    const openBtn = document.getElementById("open-transfer-modal");
    const closeBtn = document.getElementById("close-transfer-modal");
    const cancelBtn = document.getElementById("cancel-transfer-modal");
    const form = document.getElementById("transfer-form");
    const submitBtn = document.getElementById("submit-transfer-btn");
    const transferTypeSelect = document.getElementById("transfer-type");
    const chainSelectGroup = document.getElementById("chain-select-group");
    const errorAlert = document.getElementById("modal-error-alert");
    const successAlert = document.getElementById("modal-success-alert");

    function openModal() {
        resetForm();
        modal.classList.remove("hidden");
    }

    function closeModal() {
        modal.classList.add("hidden");
    }

    function resetForm() {
        form.reset();
        errorAlert.style.display = "none";
        successAlert.style.display = "none";
        submitBtn.disabled = false;
        submitBtn.innerText = "Execute Transfer";
        toggleTransferType();
    }

    function toggleTransferType() {
        if (transferTypeSelect.value === "BLOCKCHAIN_TESTNET") {
            chainSelectGroup.style.display = "flex";
            document.getElementById("recipient-label").innerText = "Destination EVM Address (0x...)";
            document.getElementById("recipient-input").placeholder = "0x71C...a08";
        } else {
            chainSelectGroup.style.display = "none";
            document.getElementById("recipient-label").innerText = "Recipient User Email";
            document.getElementById("recipient-input").placeholder = "user@coinpilot.internal";
        }
    }

    if (openBtn) openBtn.addEventListener("click", openModal);
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (cancelBtn) cancelBtn.addEventListener("click", closeModal);
    if (transferTypeSelect) transferTypeSelect.addEventListener("change", toggleTransferType);

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            errorAlert.style.display = "none";
            successAlert.style.display = "none";

            const transferType = transferTypeSelect.value;
            const recipient = document.getElementById("recipient-input").value.trim();
            const amount = document.getElementById("amount-input").value.trim();
            const chainId = document.getElementById("chain-select").value;
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
            const idempotencyKey = "tx_" + Date.now() + "_" + Math.random().toString(36).substring(2, 9);

            submitBtn.disabled = true;
            submitBtn.innerText = "Broadcasting...";

            let endpoint = "";
            let payload = {};

            if (transferType === "INTERNAL_CREDIT") {
                endpoint = "/api/v1/transfers/internal";
                payload = { recipient_email: recipient, amount: amount, idempotency_key: idempotencyKey };
            } else {
                endpoint = "/api/v1/transfers/blockchain";
                payload = { recipient_address: recipient, amount: amount, chain_id: parseInt(chainId, 10), idempotency_key: idempotencyKey };
            }

            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken,
                    },
                    body: JSON.stringify(payload),
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Transfer failed. Please check inputs.");
                }

                successAlert.innerText = data.message || "Transaction registered successfully.";
                successAlert.style.display = "block";

                setTimeout(() => {
                    window.location.reload();
                }, 1500);

            } catch (err) {
                errorAlert.innerText = err.message;
                errorAlert.style.display = "block";
                submitBtn.disabled = false;
                submitBtn.innerText = "Execute Transfer";
            }
        });
    }
});
