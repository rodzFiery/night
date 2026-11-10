document.addEventListener("DOMContentLoaded", () => {
    const year = document.getElementById("current-year");
    if (year) year.textContent = String(new Date().getFullYear());

    const menuButton = document.querySelector(".launch-menu-toggle");
    const navigation = document.getElementById("launch-nav");

    if (menuButton && navigation) {
        menuButton.addEventListener("click", () => {
            const open = navigation.classList.toggle("is-open");
            menuButton.setAttribute("aria-expanded", String(open));
            menuButton.setAttribute("aria-label", open ? "Close menu" : "Open menu");
        });

        navigation.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => {
                navigation.classList.remove("is-open");
                menuButton.setAttribute("aria-expanded", "false");
                menuButton.setAttribute("aria-label", "Open menu");
            });
        });
    }
});