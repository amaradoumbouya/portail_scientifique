(function () {
    var script = document.currentScript;
    var timeoutSec = parseInt(script && script.getAttribute("data-timeout"), 10);
    if (!timeoutSec || timeoutSec < 1) {
        timeoutSec = 30 * 60;
    }
    var logoutUrl = (script && script.getAttribute("data-logout-url")) || "/deconnexion/";
    var loginUrl = (script && script.getAttribute("data-login-url")) || "/connexion/?inactivite=1";
    var keepaliveUrl = script && script.getAttribute("data-keepalive-url");
    var timeoutMs = timeoutSec * 1000;
    var pingEveryMs = Math.min(60 * 1000, Math.max(15 * 1000, timeoutMs / 4));
    var timer = null;
    var lastPing = 0;
    var loggingOut = false;

    function csrfToken() {
        var match = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    function expireSession() {
        if (loggingOut) {
            return;
        }
        loggingOut = true;
        var token = csrfToken();
        var form = new FormData();
        form.append("csrfmiddlewaretoken", token);
        fetch(logoutUrl, {
            method: "POST",
            body: form,
            credentials: "same-origin",
            headers: {
                "X-CSRFToken": token,
                "X-Requested-With": "XMLHttpRequest"
            }
        }).finally(function () {
            window.location.href = loginUrl;
        });
    }

    function pingServer() {
        if (loggingOut || !keepaliveUrl) {
            return;
        }
        fetch(keepaliveUrl, {
            method: "GET",
            credentials: "same-origin",
            redirect: "manual",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        }).then(function (response) {
            if (response.status === 401 || (response.status >= 300 && response.status < 400)) {
                loggingOut = true;
                window.location.href = loginUrl;
            }
        }).catch(function () {});
    }

    function resetTimer() {
        if (loggingOut) {
            return;
        }
        if (timer) {
            window.clearTimeout(timer);
        }
        timer = window.setTimeout(expireSession, timeoutMs);
        var now = Date.now();
        if (now - lastPing >= pingEveryMs) {
            lastPing = now;
            pingServer();
        }
    }

    ["click", "keydown", "mousemove", "scroll", "touchstart"].forEach(function (eventName) {
        document.addEventListener(eventName, resetTimer, { passive: true });
    });
    resetTimer();
})();
