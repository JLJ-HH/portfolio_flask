const QUESTIONS_PER_PAGE = 5;

let currentQuestions = [];
let currentLang = '';
let timeLeft = 20 * 60; // 20 Minuten
let timerInterval;
let currentPage = 0;
let userAnswers = {};

// Lädt Fragen aus JSON und wählt eine bestimmte Anzahl random aus
async function loadQuestionsFromFile(lang, count) {
  // Update paths for Flask static folder
  const url = lang === 'de' ? '/scrum-quiz/static/data/questions_de.json' : '/scrum-quiz/static/data/questions_en.json';
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Fehler beim Laden der Fragen.');
    const allQuestions = await response.json();

    // Max Fragen begrenzen auf das was vorhanden ist
    const finalCount = Math.min(count, allQuestions.length);

    // Shuffle (mischen)
    const shuffled = allQuestions.sort(() => Math.random() - 0.5);
    // Gewählte Anzahl auswählen
    currentQuestions = shuffled.slice(0, finalCount);
  } catch (error) {
    console.error('Fragen konnten nicht geladen werden:', error);
    alert(lang === 'de' ? 'Die Fragen konnten nicht geladen werden.' : 'Failed to load questions.');
  }
}

async function startQuiz(lang) {
  const inputEl = document.getElementById('questionCountInput');
  const requestedCount = parseInt(inputEl.value) || 30;

  currentLang = lang;
  await loadQuestionsFromFile(lang, requestedCount);

  // Zeit dynamisch berechnen: 0,75 Min pro Frage (80 Fragen = 60 Min)
  timeLeft = Math.floor(currentQuestions.length * 0.75 * 60);
  
  currentPage = 0;
  userAnswers = {};

  document.getElementById('startPage').classList.add('hidden');
  document.getElementById('quizPage').classList.remove('hidden');

  const quizTitle = document.getElementById('quizTitle');
  quizTitle.textContent = lang === 'de' ? 'PSM1 Scrum Quiz' : 'PSM1 Scrum Quiz';
  quizTitle.lang = lang;
  quizTitle.tabIndex = -1;

  document.getElementById('submitBtn').textContent = lang === 'de' ? 'Abschicken' : 'Submit';
  document.getElementById('backBtn').textContent = lang === 'de' ? 'Zurück zur Sprache wählen' : 'Back to Language Selection';

  resetQuiz();
  loadQuestions();
  updateProgress();
  startTimer();

  // Fokus auf Titel setzen für Screenreader
  quizTitle.focus();
}

function resetQuiz() {
  clearInterval(timerInterval);
  updateTimerDisplay();
  document.getElementById('quizForm').innerHTML = '';
  document.getElementById('result').textContent = '';
  document.getElementById('feedback').innerHTML = '';
  document.getElementById('feedback').className = '';
  document.getElementById('feedback').style.display = 'none';
  document.getElementById('submitBtn').disabled = false;
  document.getElementById('repeatBtn').style.display = 'none';
}

function loadQuestions() {
  const form = document.getElementById('quizForm');
  form.innerHTML = '';

  const start = currentPage * QUESTIONS_PER_PAGE;
  const end = Math.min(start + QUESTIONS_PER_PAGE, currentQuestions.length);

  for (let i = start; i < end; i++) {
    const q = currentQuestions[i];
    const div = document.createElement('div');
    div.className = 'question';

    const questionId = `question${i}`;
    div.setAttribute('aria-labelledby', questionId);
    div.innerHTML = `<h3 id="${questionId}">${i + 1}. ${q.question}</h3>`;

    const selectedAnswer = userAnswers[i];

    q.answers.forEach((answer, idx) => {
      const id = `q${i}_a${idx}`;
      div.innerHTML += `
        <label for="${id}">
          <input type="radio" name="q${i}" id="${id}" value="${idx}" ${selectedAnswer === idx ? 'checked' : ''} />
          ${answer}
        </label>`;
    });

    form.appendChild(div);
  }

  form.querySelectorAll('input[type=radio]').forEach(input => {
    input.addEventListener('change', (event) => {
      const name = event.target.name;
      const qIndex = parseInt(name.substring(1));
      userAnswers[qIndex] = parseInt(event.target.value);
      updateProgress();
    });
  });

  updateNavigationButtons();

  // Fokus auf erste Antwort setzen für bessere Zugänglichkeit
  const firstInput = document.querySelector('.question input');
  if (firstInput) firstInput.focus();
}

function updateNavigationButtons() {
  const navDiv = document.getElementById('navigationButtons');
  navDiv.innerHTML = '';

  if (currentPage > 0) {
    const btnPrev = document.createElement('button');
    btnPrev.textContent = currentLang === 'de' ? 'Zurück' : 'Previous';
    btnPrev.type = 'button';
    btnPrev.onclick = () => { currentPage--; loadQuestions(); };
    btnPrev.style.marginRight = '10px';
    navDiv.appendChild(btnPrev);
  }

  if ((currentPage + 1) * QUESTIONS_PER_PAGE < currentQuestions.length) {
    const btnNext = document.createElement('button');
    btnNext.textContent = currentLang === 'de' ? 'Weiter' : 'Next';
    btnNext.type = 'button';
    btnNext.onclick = () => { currentPage++; loadQuestions(); };
    navDiv.appendChild(btnNext);
    document.getElementById('submitBtn').style.display = 'none';
  } else {
    document.getElementById('submitBtn').style.display = 'inline-block';
  }
}

function updateTimerDisplay() {
  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  document.getElementById('timer').textContent = (currentLang === 'de' ? 'Verbleibende Zeit: ' : 'Time left: ')
    + `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function startTimer() {
  timerInterval = setInterval(() => {
    timeLeft--;
    updateTimerDisplay();
    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      alert(currentLang === 'de' ? 'Zeit ist abgelaufen! Das Quiz wird nun ausgewertet.' : 'Time is up! The quiz will now be submitted.');
      checkAnswers();
      document.getElementById('submitBtn').disabled = true;
    }
  }, 1000);
}

function updateProgress() {
  const total = currentQuestions.length;
  let answered = Object.keys(userAnswers).length;
  document.getElementById('progress').textContent = (currentLang === 'de' ? 'Beantwortete Fragen: ' : 'Answered questions: ') + `${answered} / ${total}`;
}

function checkAnswers() {
  const totalQuestions = currentQuestions.length;
  const pointsPerQuestion = 100 / totalQuestions;
  let scorePoints = 0;
  let unanswered = 0;
  const feedback = [];
  const feedbackDiv = document.getElementById('feedback');
  feedbackDiv.innerHTML = '';

  currentQuestions.forEach((q, i) => {
    const selectedAnswer = userAnswers[i];
    if (selectedAnswer === undefined) {
      unanswered++;
      return;
    }
    if (selectedAnswer === q.correct) {
      scorePoints += pointsPerQuestion;
    } else {
      feedback.push({
        questionNum: i + 1,
        correctAnswer: q.answers[q.correct]
      });
    }
  });

  const resultDiv = document.getElementById('result');
  if (unanswered > 0) {
    resultDiv.textContent = currentLang === 'de'
      ? `Bitte beantworte alle Fragen! Noch offen: ${unanswered}`
      : `Please answer all questions! Remaining: ${unanswered}`;
    return;
  }

  const scoreRounded = Math.round(scorePoints * 10) / 10;
  const percentage = ((scorePoints / 100) * 100).toFixed(1);

  resultDiv.textContent = currentLang === 'de'
    ? `Dein Ergebnis: ${scoreRounded} von 100 Punkten (${percentage}%)`
    : `Your score: ${scoreRounded} out of 100 points (${percentage}%)`;

  if (feedback.length > 0) {
    let fbHTML = '';
    feedback.forEach(f => {
      fbHTML += `<div>${currentLang === 'de' ? `Frage ${f.questionNum} falsch beantwortet.` : `Question ${f.questionNum} answered incorrectly.`}<br>${currentLang === 'de' ? 'Richtige Antwort:' : 'Correct answer:'} <strong>${f.correctAnswer}</strong></div>`;
    });
    feedbackDiv.innerHTML = fbHTML;
  }

  const passed = parseFloat(percentage) >= 80;
  feedbackDiv.style.display = 'block';
  feedbackDiv.className = passed ? 'feedback-success' : 'feedback-error';

  if (passed && feedback.length === 0) {
    feedbackDiv.innerHTML = `<div>${currentLang === 'de' ? 'Herzlichen Glückwunsch! Du hast alle Fragen richtig beantwortet.' : 'Congratulations! You answered all questions correctly.'}</div>`;
  }

  clearInterval(timerInterval);
  document.getElementById('submitBtn').disabled = true;
  document.getElementById('repeatBtn').style.display = 'block';
  document.getElementById('repeatBtn').textContent = currentLang === 'de' ? 'Quiz wiederholen' : 'Repeat Quiz';
}

function backToStart() {
  clearInterval(timerInterval);
  document.getElementById('quizPage').classList.add('hidden');
  document.getElementById('startPage').classList.remove('hidden');
  resetQuiz();
}
