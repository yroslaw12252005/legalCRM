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
    let currentStep = Math.max(0, parseInt(config.dataset.step || "0", 10));
    let highlighted = null;
    const isSolo = config.dataset.isSolo === "true";
    const steps = [
      { title:"Добро пожаловать в rossCRM", text:"Проведём вас по главным рабочим страницам CRM. Вы увидите настоящий интерфейс каждого раздела, но обучение ничего не создаст и не изменит.", center:true },
      { target:"[data-tour='sidebar']", title:"Главное меню", text:"Через это меню вы переходите между рабочими разделами компании. Во время обучения мы последовательно откроем самые важные из них." },
      { url:config.dataset.currentApplicationsUrl, target:"[data-tour='current-applications-interface']", title:"Первичка", text:"Здесь отображаются актуальные обращения. Из списка можно открыть заявку, проверить последнее изменение и начать первичную обработку." },
      { url:config.dataset.addRecordUrl, target:"[data-tour='add-record-interface']", title:"Создание заявки", text:"В этой форме вручную добавляют клиента, контакты, источник обращения и ответственных сотрудников. Сейчас заполнять или сохранять форму не нужно." },
      { url:config.dataset.allLeadsUrl, target:"[data-tour='lead-filters']", title:"Поиск и фильтры", text:"На странице всех заявок можно искать по имени, телефону, ID и номеру договора, а также сочетать несколько фильтров." },
      { url:config.dataset.allLeadsUrl, target:"[data-tour='lead-list']", title:"Реестр заявок", text:"Это основной список клиентов компании. Отсюда открывают карточку дела, меняют статус и выполняют массовые действия с выбранными заявками." },
      { url:config.dataset.tasksUrl, target:"[data-tour='tasks-interface']", title:"Задачи", text:"В разделе видны поручения, сроки и приоритеты. Здесь же администратор создаёт новую задачу сотруднику." },
      { url:config.dataset.calendarUrl, target:"[data-tour='calendar-interface']", title:"Рабочий календарь", text:"Календарь собирает записи в офис, созвоны, доплаты и другие события по датам." },
      { url:config.dataset.walletUrl, target:"[data-tour='wallet-interface']", title:"Кошелёк компании", text:"Здесь отображаются баланс, способ пополнения и история всех операций по счёту компании." },
      { url:config.dataset.salaryUrl, target:"[data-tour='salary-filter']", title:"Период расчёта зарплаты", text:"Выберите месяц и половину месяца, затем сформируйте расчёт или скачайте ведомость Excel." },
      { url:config.dataset.salaryUrl, target:"[data-tour='salary-table']", title:"Ведомость сотрудников", text:"Таблица показывает расчётную базу и итоговую зарплату. Нажатие на имя открывает подробный расчёт сотрудника." },
      { url:config.dataset.registerEmployeeUrl, target:"[data-tour='register-employee-interface']", title:"Новый сотрудник", text:"Здесь создают учётную запись, назначают роль и задают условия зарплаты: процент, оклад или их сочетание.", teamOnly:true },
      { url:config.dataset.employeesUrl, target:"[data-tour='employees-interface']", title:"Список сотрудников", text:"В списке можно открыть сотрудника для редактирования или отключить его учётную запись, сохранив историю назначений.", teamOnly:true },
      { url:config.dataset.addBranchUrl, target:"[data-tour='add-branch-interface']", title:"Новый филиал", text:"Форма добавляет подразделение компании. После этого сотрудников и заявки можно распределять по филиалам.", teamOnly:true },
      { url:config.dataset.branchesUrl, target:"[data-tour='branches-interface']", title:"Филиалы компании", text:"Здесь отображается структура компании и доступен переход к данным каждого филиала.", teamOnly:true },
      { url:config.dataset.leadExchangeUrl, target:"[data-tour='lead-exchange-interface']", title:"Биржа заявок", text:"В этом разделе настраивают потоковое получение лидов и работают с доступными предложениями на бирже." },
      { url:config.dataset.tildaUrl, target:"[data-tour='tilda-interface']", title:"Интеграция с Tilda", text:"Создайте подключение формы сайта, получите адрес webhook и ключ — новые обращения будут автоматически попадать в CRM." },
      { url:config.dataset.knowledgeBaseUrl, target:"[data-tour='knowledge-base-interface']", title:"База знаний", text:"Здесь хранятся внутренние инструкции и материалы компании. Администратор может добавлять категории и документы." },
      { url:config.dataset.callRecordingsUrl, target:"[data-tour='call-recordings-interface']", title:"Записи разговоров", text:"Раздел позволяет найти звонок по номеру телефона, увидеть сотрудника и скачать запись разговора." },
      { title:"Обучение завершено", text:"Теперь вы знаете, где находятся основные инструменты rossCRM. В любой момент обучение можно запустить заново кнопкой «Пройти обучение» в меню администратора.", center:true }
    ].filter(function(step){ return !(step.teamOnly && isSolo); });
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
    function routePath(url) {
      return new URL(url, window.location.origin).pathname.replace(/\/+$/, "") || "/";
    }
    function openRoute(url) {
      const destination = new URL(url, window.location.origin);
      destination.searchParams.set("tour", "1");
      window.location.assign(destination.pathname + destination.search + destination.hash);
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
      if (step.url && routePath(window.location.href)!==routePath(step.url)) { openRoute(step.url); return; }
      let target=step.target?document.querySelector(step.target):null;
      while (step.target && !target && currentStep<steps.length-1) {
        currentStep+=1; await sendAction("progress",currentStep); step=steps[currentStep];
        if (step.url && routePath(window.location.href)!==routePath(step.url)) { openRoute(step.url); return; }
        target=step.target?document.querySelector(step.target):null;
      }
      overlay.hidden=false; tooltip.hidden=false; document.body.classList.add("crm-tour-active"); openMobileNavigation(target);
      if (target) {
        target.scrollIntoView({behavior:"smooth",block:target.offsetHeight>window.innerHeight*.72?"start":"center",inline:"nearest"});
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
