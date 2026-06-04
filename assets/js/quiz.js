(function(){
  const KEY = "quiz_done_3h";
  const DELAY = 5000; // 5 secondes

  function hasDoneQuiz(){ return localStorage.getItem(KEY) === "true"; }
  function setDoneQuiz(){ localStorage.setItem(KEY, "true"); }

  function showOverlay(){
    const el = document.getElementById("quizOverlay");
    if(!el) return;
    el.style.display = "flex";
    document.body.style.overflow = "hidden";
  }
  function hideOverlay(){
    const el = document.getElementById("quizOverlay");
    if(!el) return;
    el.style.display = "none";
    document.body.style.overflow = "";
    setDoneQuiz();
  }

  document.addEventListener("DOMContentLoaded", () => {
    const isHome = document.body.dataset.page === "home";
    const overlayExists = !!document.getElementById("quizOverlay");

    // Boutons ouvrir le quiz
    document.querySelectorAll("[data-quiz-open]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        if(btn.tagName === "A" && btn.getAttribute("href") !== "quiz.html"){
          e.preventDefault();
          showOverlay();
        }
      });
    });

    // Boutons fermer
    document.querySelectorAll("[data-quiz-close]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        hideOverlay();
      });
    });

    // Fermer sur clic fond
    const overlay = document.getElementById("quizOverlay");
    if(overlay){
      overlay.addEventListener("click", (e) => {
        if(e.target === overlay) hideOverlay();
      });
    }

    // Fermer avec Escape
    document.addEventListener("keydown", (e) => {
      if(e.key === "Escape") hideOverlay();
    });

    // Pop-up auto après 5s, 1ère visite, page accueil uniquement
    if(isHome && overlayExists && !hasDoneQuiz()){
      setTimeout(showOverlay, DELAY);
    }
  });

  window.ThreeHQuiz = { setDoneQuiz, hideOverlay, showOverlay };
})();
