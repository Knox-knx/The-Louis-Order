document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".roles-grid label").forEach(label => {

        const checkbox = label.querySelector(
            'input[type="checkbox"]'
        );

        function updateState() {

            if (checkbox.checked) {

                label.style.background =
                    "#D4AF37";

                label.style.color =
                    "#000";

                label.style.borderColor =
                    "#D4AF37";

                label.style.boxShadow =
                    "0 0 15px rgba(212,175,55,.35)";

            } else {

                label.style.background =
                    "#111";

                label.style.color =
                    "#fff";

                label.style.borderColor =
                    "rgba(212,175,55,.15)";

                label.style.boxShadow =
                    "none";
            }
        }

        updateState();

        checkbox.addEventListener(
            "change",
            updateState
        );

    });

});