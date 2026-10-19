document.addEventListener("DOMContentLoaded", () => {
    const notificationContainer = document.getElementById("notification-list");

    async function refreshNotifications() {
        if (!notificationContainer) return;
        try {
            const res = await fetch("/api/v1/notifications");
            if (!res.ok) return;
            const data = await res.json();
            if (data.notifications && data.notifications.length > 0) {
                notificationContainer.innerHTML = data.notifications.map(n => `
                    <div class="alert ${n.category === 'DANGER' ? 'alert-danger' : n.category === 'SUCCESS' ? 'alert-success' : 'alert-info'}" style="margin-bottom: 0.5rem; padding: 0.75rem 1rem;">
                        <div>
                            <div style="font-weight: 600;">${escapeHtml(n.title)}</div>
                            <div style="font-size: 0.825rem;">${escapeHtml(n.message)}</div>
                        </div>
                        <span style="font-size: 0.75rem; color: var(--text-muted);">${new Date(n.created_at).toLocaleTimeString()}</span>
                    </div>
                `).join('');
            }
        } catch (err) {
            console.error("Failed to load notifications:", err);
        }
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    setInterval(refreshNotifications, 30000);
});
