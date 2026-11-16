(function () {
  "use strict";
  function readCookie(name) {
    const row = document.cookie.split("; ").find((item) => item.startsWith(name + "="));
    return row ? decodeURIComponent(row.split("=").slice(1).join("=")) : "";
  }
  document.addEventListener("DOMContentLoaded", function () {
    const config = document.getElementById("crm-onboarding-config");
    if (!config || config.dataset.autoStart !== "true") return;
    const overlay = document.getElementById("crm-tour-overlay");
    const tooltip = document.getElementById("crm-tour-tooltip");
    const title = document.getElementById("crm-tour-title");
    const description = document.getElementById("crm-tour-description");
    const progress = document.getElementById("crm-tour-progress");
    const progressValue = document.getElementById("crm-tour-progress-value");
    const backButton = document.getElementById("crm-tour-back");
    const nextButton = document.getElementById("crm-tour-next");
    const skipButton = document.getElementById("crm-tour-skip");
    const closeButton = document.getElementById("crm-tour-close");
    const allLeadsPath = new URL(config.dataset.allLeadsUrl, window.location.origin).pathname;
    let currentStep = Math.max(0, parseInt(config.dataset.step || "0", 10));
    let highlighted = null;
    const steps = [
      { title:"Добро пожаловать в rossCRM", text:"За несколько минут покажем основные разделы и рабочий путь администратора — от новой заявки до контроля сотрудников.", center:true },
      { target:"[data-tour='sidebar']", title:"Главное меню", text:"Здесь собраны все рабочие разделы компании. Состав меню зависит от роли сотрудника и формата компании." },
      { target:"[data-tour='create-lead']", title:"Создание заявки", text:"Добавляйте клиента вручную: контакты, направление обращения, источник и первичный комментарий." },
      { target:"[data-tour='primary-leads']", title:"Первичка", text:"Раздел показывает свежие заявки и помогает быстро обработать первичное обращение клиента." },
      { target:"[data-tour='all-leads']", title:"Все заявки", text:"Полный реестр клиентов компании: статусы, ответственные сотрудники, оплаты и переход в карточку дела." },
      { target:"[data-tour='lead-filters']", path:allLeadsPath, title:"Поиск и фильтры", text:"Находите заявки по имени, телефону, ID или номеру договора и сочетайте несколько фильтров одновременно." },
      { target:"[data-tour='lead-list']", path:allLeadsPath, title:"Работа со списком", text:"Откройте клиента нажатием на имя. Выбранные заявки можно массово передавать в работу, назначать сотрудникам и менять их статус." },
      { target:"[data-tour='tasks']", title:"Задачи", text:"Создавайте поручения сотрудникам и контролируйте сроки выполнения в одном списке." },
      { target:"[data-tour='calendar']", title:"Рабочий календарь", text:"Календарь помогает видеть записи в офис, звонки и другие события по датам." },
      { target:"[data-tour='wallet']", title:"Баланс компании", text:"Здесь отображается текущий баланс для сервисов CRM и переход к истории пополнений." },
      { target:"[data-tour='salary']", title:"Расчёт зарплаты", text:"Формируйте расчёт за выбранный период и выгружайте ведомость по сотрудникам." },
      { target:"[data-tour='employees']", title:"Добавление сотрудников", text:"Создавайте учётные записи, назначайте роли и задавайте тип зарплаты. В одиночной компании этот шаг не требуется." },
      { target:"[data-tour='branches']", title:"Филиалы", text:"Разделяйте сотрудников и заявки между филиалами компании. В одиночной компании шаг будет пропущен." },
      { target:"[data-tour='tilda']", title:"Интеграция с Tilda", text:"Подключите формы сайта, чтобы новые обращения автоматически создавались в CRM." },
      { target:"[data-tour='knowledge-base']", title:"База знаний", text:"Храните внутренние инструкции и материалы, которые должны быть доступны сотрудникам." },
      { title:"Готово к работе", text:"Начните с создания заявки или настройте сотрудников и интеграцию с сайтом. Повторно запустить обучение можно кнопкой в меню администратора.", center:true }
    ];
    async function sendAction(action, step) {
      const body = new URLSearchParams({action:action});
      if (typeof step === "number") body.set("step", String(step));
      try {
        await fetch(config.dataset.updateUrl, {method:"POST", credentials:"same-origin", headers:{"Content-Type":"application/x-www-form-urlencoded;charset=UTF-8","X-CSRFToken":readCookie("csrftoken")}, body:body.toString()});
      } catch (error) { /* Progress will be retried on the next interaction. */ }
    }
    function removeHighlight() {
      if (highlighted) {
        highlighted.classList.remove("crm-tour-highlight");
        if (highlighted.dataset.crmTourPositionChanged === "true") {
          highlighted.style.position = "";
          delete highlighted.dataset.crmTourPositionChanged;
        }
      }
      highlighted = null;
    }
    function closeTour() {
      removeHighlight(); overlay.hidden=true; tooltip.hidden=true; document.body.classList.remove("crm-tour-active");
      const navToggle=document.getElementById("crm-nav-toggle"); if (navToggle) navToggle.checked=false;
    }
    function openMobileNavigation(target) {
      const navToggle=document.getElementById("crm-nav-toggle");
      if (navToggle && target && target.closest("nav") && window.innerWidth<=768) navToggle.checked=true;
    }
    function positionTooltip(target, centered) {
      tooltip.classList.toggle("crm-tour-tooltip--center", centered);
      tooltip.style.top=""; tooltip.style.left=""; tooltip.style.bottom=""; tooltip.style.transform="";
      if (centered || !target || window.innerWidth<=640) return;
      const rect=target.getBoundingClientRect(); const tipRect=tooltip.getBoundingClientRect(); const gap=18;
      let left=rect.right+gap; let top=rect.top+Math.min(10,rect.height/3);
      if (left+tipRect.width>window.innerWidth-14) left=rect.left-tipRect.width-gap;
      if (left<14) { left=Math.max(14,Math.min(rect.left,window.innerWidth-tipRect.width-14)); top=rect.bottom+gap; }
      if (top+tipRect.height>window.innerHeight-14) top=Math.max(14,window.innerHeight-tipRect.height-14);
      tooltip.style.left=left+"px"; tooltip.style.top=top+"px";
    }
    async function showStep(index) {
      removeHighlight(); currentStep=Math.max(0,Math.min(index,steps.length-1)); let step=steps[currentStep];
      if (step.path && window.location.pathname!==step.path) { window.location.assign(step.path+"?tour=1"); return; }
      let target=step.target?document.querySelector(step.target):null;
      while (step.target && !target && currentStep<steps.length-1) {
        currentStep+=1; await sendAction("progress",currentStep); step=steps[currentStep];
        if (step.path && window.location.pathname!==step.path) { window.location.assign(step.path+"?tour=1"); return; }
        target=step.target?document.querySelector(step.target):null;
      }
      overlay.hidden=false; tooltip.hidden=false; document.body.classList.add("crm-tour-active"); openMobileNavigation(target);
      if (target) {
        target.scrollIntoView({behavior:"smooth",block:"center",inline:"nearest"});
        if (window.getComputedStyle(target).position === "static") {
          target.style.position = "relative";
          target.dataset.crmTourPositionChanged = "true";
        }
        target.classList.add("crm-tour-highlight"); highlighted=target;
      }
      title.textContent=step.title; description.textContent=step.text;
      progress.textContent="Шаг "+(currentStep+1)+" из "+steps.length;
      progressValue.style.width=(((currentStep+1)/steps.length)*100)+"%";
      backButton.disabled=currentStep===0;
      nextButton.textContent=currentStep===0?"Начать":(currentStep===steps.length-1?"Завершить":"Далее");
      skipButton.textContent=currentStep===0?"Пропустить обучение":"Пропустить";
      window.setTimeout(function(){ positionTooltip(target,Boolean(step.center)); nextButton.focus({preventScroll:true}); },target?260:0);
    }
    nextButton.addEventListener("click",async function(){
      if (currentStep>=steps.length-1) { await sendAction("complete"); closeTour(); return; }
      const next=currentStep+1; await sendAction("progress",next); showStep(next);
    });
    backButton.addEventListener("click",async function(){ if(currentStep===0)return; const previous=currentStep-1; await sendAction("progress",previous); showStep(previous); });
    skipButton.addEventListener("click",async function(){ await sendAction("skip"); closeTour(); });
    closeButton.addEventListener("click",async function(){ await sendAction("defer"); closeTour(); });
    window.addEventListener("resize",function(){ if(!tooltip.hidden) positionTooltip(highlighted,Boolean(steps[currentStep].center)); });
    document.addEventListener("keydown",function(event){ if(event.key==="Escape"&&!tooltip.hidden) closeButton.click(); });
    showStep(currentStep);
  });
})();
