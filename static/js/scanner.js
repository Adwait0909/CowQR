(function () {
  var statusEl = document.getElementById("qr-reader-status");

  if (!statusEl) {
    console.error("QR reader status element not found.");
    return;
  }

  if (typeof Html5Qrcode === "undefined") {
    statusEl.textContent =
      "Scanner library failed to load. Check your internet connection.";
    return;
  }

  var readerEl = document.getElementById("qr-reader");

  if (!readerEl) {
    statusEl.textContent = "QR scanner element not found.";
    return;
  }

  var html5QrCode = new Html5Qrcode("qr-reader");
  var hasHandledResult = false;

  function onScanSuccess(decodedText) {
    if (hasHandledResult) return;

    hasHandledResult = true;
    statusEl.textContent = "Tag recognized. Opening passport...";

    html5QrCode
      .stop()
      .then(function () {
        var target = decodedText.trim();

        var looksLikeUrl = /^https?:\/\//i.test(target);

        if (looksLikeUrl) {
          window.location.href = target;
        } else {
          window.location.href =
            "/cow/" + encodeURIComponent(target);
        }
      })
      .catch(function () {
        window.location.href = decodedText;
      });
  }

  function onScanFailure() {
    // Ignore continuous scan failures while searching for a QR code.
  }

  var config = {
    fps: 10,
    qrbox: {
      width: 250,
      height: 250
    },
    aspectRatio: 1.0
  };

  statusEl.textContent = "Starting camera...";

  html5QrCode
    .start(
      { facingMode: "environment" },
      config,
      onScanSuccess,
      onScanFailure
    )
    .then(function () {
      statusEl.textContent =
        "Camera active — point it at a cow's QR tag.";
    })
    .catch(function (err) {
      statusEl.textContent =
        "Could not start the camera. Please allow camera access and use HTTPS.";

      console.error("Camera error:", err);
    });
})();
