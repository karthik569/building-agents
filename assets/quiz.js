/* ==========================================================================
   quiz.js — retrieval-practice widget.
   Markup contract (one block per quiz, any number of questions):

     <div class="quiz" data-quiz>
       <div class="quiz-q" data-answer="a">
         <p class="quiz-prompt"><span class="qnum">01</span>Question text?</p>
         <div class="quiz-opts">
           <button class="quiz-opt" data-opt="a"><span class="key">A</span>...</button>
           ...
         </div>
         <p class="quiz-why"><b>Why:</b> ...</p>
       </div>
     </div>

   Behaviour: first click locks the question, marks right/wrong, reveals the
   explanation. No score is shown until every question is attempted, so the
   learner cannot calibrate off a running total.
   ========================================================================== */

(function () {
  "use strict";

  var keyFor = function (el) {
    return el.getAttribute("data-opt");
  };

  function initQuiz(quiz) {
    var questions = Array.prototype.slice.call(quiz.querySelectorAll(".quiz-q"));
    if (!questions.length) return;

    var scoreEl = quiz.querySelector(".quiz-score");
    var answered = 0;
    var correct = 0;

    questions.forEach(function (q) {
      var answer = q.getAttribute("data-answer");
      var opts = Array.prototype.slice.call(q.querySelectorAll(".quiz-opt"));
      var why = q.querySelector(".quiz-why");

      opts.forEach(function (btn) {
        btn.addEventListener("click", function () {
          if (q.dataset.done) return;
          q.dataset.done = "1";

          var picked = keyFor(btn);
          var isRight = picked === answer;

          opts.forEach(function (o) {
            o.disabled = true;
            if (keyFor(o) === answer) o.classList.add("correct");
          });
          if (!isRight) btn.classList.add("wrong");

          if (why) why.classList.add("show");

          answered += 1;
          if (isRight) correct += 1;

          if (answered === questions.length && scoreEl) {
            scoreEl.innerHTML =
              "Attempted <b>" + answered + " of " + questions.length +
              "</b> — got <b>" + correct + "</b> right first time. " +
              (correct === questions.length
                ? "Solid. Come back tomorrow and try to beat this without rereading."
                : "Reread only the explanation for the ones you missed, then close the page and retry.");
            scoreEl.hidden = false;
          }
        });
      });
    });

    if (scoreEl) scoreEl.hidden = true;
  }

  function boot() {
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-quiz]"),
      initQuiz
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
