const menuBtn = document.getElementById("menuBtn");
const navLinks = document.getElementById("navLinks");

if (menuBtn && navLinks) {
  menuBtn.addEventListener("click", () => {
    navLinks.classList.toggle("active");
  });
}

const revealElements = document.querySelectorAll(".reveal");

function revealOnScroll() {
  revealElements.forEach((element) => {
    const elementTop = element.getBoundingClientRect().top;
    const windowHeight = window.innerHeight;

    if (elementTop < windowHeight - 80) {
      element.classList.add("active");
    }
  });
}

window.addEventListener("scroll", revealOnScroll);
window.addEventListener("load", revealOnScroll);

const questions = document.querySelectorAll(".question");
const nextButtons = document.querySelectorAll(".next-btn");

let currentQuestion = 0;

nextButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const current = questions[currentQuestion];
    const input = current.querySelector("input, select");

    if (!input.checkValidity()) {
      input.reportValidity();
      return;
    }

    current.classList.remove("active");
    currentQuestion++;

    questions[currentQuestion].classList.add("active");
  });
});

const progressBars = document.querySelectorAll(".progress-fill");

progressBars.forEach((bar) => {
  const progress = bar.dataset.progress;
  bar.style.width = `${progress}%`;
});