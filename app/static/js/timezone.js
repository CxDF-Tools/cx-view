(function () {
    const STORAGE_KEY = "cxview_display_tz";
    const DEFAULT_TZ = "America/Chicago";

    function resolveZone(value) {
        return value === "local" ? Intl.DateTimeFormat().resolvedOptions().timeZone : value;
    }

    function formatAll(tzValue) {
        const zone = resolveZone(tzValue);
        const formatter = new Intl.DateTimeFormat("en-US", {
            timeZone: zone,
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
            timeZoneName: "short",
        });
        document.querySelectorAll(".dt[data-utc]").forEach(function (el) {
            const iso = el.dataset.utc;
            if (!iso) return;
            const parsed = new Date(iso);
            if (isNaN(parsed.getTime())) return;
            el.textContent = formatter.format(parsed);
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        const select = document.getElementById("tz-select");
        const saved = localStorage.getItem(STORAGE_KEY) || DEFAULT_TZ;

        if (select) {
            select.value = saved;
            select.addEventListener("change", function () {
                localStorage.setItem(STORAGE_KEY, select.value);
                formatAll(select.value);
            });
        }

        formatAll(saved);
    });
})();
