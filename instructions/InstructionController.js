const InstructionClient = (function($){
    const keyWordRegex = /^{%\s*(page|header|show|hide|set|event|waitFor|makeInvisible|makeVisible)\s+(.*?)\s*%}$/;
    const isFunctionRegex = /\b[^()]+\((.*)\)/;
    const isStringOrNumberRegex = /^(\s*|\d+\.?\d*|\.\d+|\".*\"|\'.*\')$/;

    let prevInvestmentState;
    let currentPage;
    let currentPageTitle;
    let lastCompletedPage;
    let lastPage;
    let statusController;
    let currentLineNumber;
    let instructionLines;
    let expParams;
    let otherStatus;

    // Initializer
    var initialize = function(){
        currentPage = 1;
        currentPageTitle = "Introduction";
        lastCompletedPage = 0;
        lastPage = 1;
        statusController = new PlayerStatusController();
        for (const button of document.getElementsByClassName("next-button")) {
            button.addEventListener("click", nextPage);
        }
        for (const button of document.getElementsByClassName("previous-button")) {
            button.addEventListener("click", previousPage);
        }
        getParameters();
    };
      
    if (
          document.readyState === "complete" ||
          (document.readyState !== "loading" && !document.documentElement.doScroll)
    ) {
        initialize();
    } else {
        document.addEventListener("DOMContentLoaded", initialize);
    }

    function getParameters(){
        $.get("instruction_client/get_parameters", function(data) {
            loadParameters(data);
            getInstructions();
        });
    }

    function loadParameters(data) {
        if (data.error){
            alert(data.error);
            return;
        }
        const expData = data.exp_data;
        expParams = new ExperimentParameters(expData.exp_params, expData.player_data, expData.translations);
        otherStatus = expData.otherstatus;
        variableStore = {};
        Object.assign(variableStore, expParams);

        updateElementText(document.getElementById("stage"), expParams.translate("stages.Spending"));
    }

    /*
     * This method will setup the period, myStatus, and otherStatuses in a way that it looks like it is the middle of an experiment
     * Period 3, Spending Stage, 5 seconds remaining
     * 
     */
    function createExampleState() {
        const period = 3;
        for (const elem of document.getElementsByClassName("current_period")) {
            elem.textContent = period;
        }
        let myStatus;
        for (let i = 0; i < otherStatus.length; ++i) {
            const other = otherStatus[i];
            if (other.displayname === expParams.displayname) {
                myStatus = other;
                other.age = period;
                other.shocks = 1;
                other.shockProb = expParams.grossShockProbability(period, other.shocks);
                other.fitness = 37;
                other.enjoyment = 63;
                other.budget = 13;
            } else {
                switch (i + expParams.groupidx % otherStatus.length) {
                    case 1:
                        other.age = period;
                        other.shocks = 0;
                        other.shockProb = expParams.grossShockProbability(period, other.shocks);
                        other.fitness = 32;
                        other.enjoyment = 67;
                        other.budget = 24;
                        break;
                    case 2:
                        other.age = period;
                        other.shocks = 1;
                        other.shockProb = expParams.grossShockProbability(period, other.shocks);
                        other.fitness = 41;
                        other.enjoyment = 61;
                        other.budget = -32;
                        break;
                    case 3:
                        other.age = period;
                        other.shocks = 0;
                        other.shockProb = expParams.grossShockProbability(period, other.shocks);
                        other.fitness = 38;
                        other.enjoyment = 58;
                        other.budget = 21;
                        break;
                }
            }
        }
    }

    function getInstructions(){
        $.get("instruction_client/get_instructions", setupInstructions);
    }

    function setupInstructions(data){
        currentLineNumber = 0;
        instructionLines = data.instruction_lines;
        lastPage = countPages(instructionLines);
        setupNextPage();
    }

    function countPages(lines) {
        let pageCount = 0;
        for (const line of lines) {
            if (isKeyWord(line)) {
                const [match, keyWord, command] = parseKeyWord(line);
                if (keyWord === 'page') {
                    pageCount++;
                }
            }
        }
        return pageCount;
    }

    function setupNextPage() {
        let firstLine = true;
        resetInstructionText();
        while (currentLineNumber < instructionLines.length) {
            const currentLine = instructionLines[currentLineNumber];
            if (isKeyWord(currentLine)){
                const [match, keyWord, command] = parseKeyWord(currentLine);
                if (keyWord === "page" && !firstLine) {
                    break;
                }
                handleKeyWord(keyWord, command);
            } else {
                parseInstructionLine(currentLine);
            } 
            currentLineNumber++;
            firstLine = false;
        }
    }

    function findPreviousPage() {
        let firstLine = true;
        let pageCount = 0; // need 2
        while (currentLineNumber > 0) {
            const currentLine = instructionLines[currentLineNumber];
            if (isKeyWord(currentLine)){
                const [match, keyWord, command] = parseKeyWord(currentLine);
                if (keyWord === "page" && !firstLine) {
                    pageCount++;
                    if (pageCount == 2) {
                        break;
                    }
                }
            }
            currentLineNumber--;
            firstLine = false;
        }
    }

    function resetInstructionText() {
        for (const elem of document.getElementsByClassName('instruction_text')) {
            elem.innerHTML = "";
        }
    }

    function parseInstructionLine(line) {
        const variables = line.match(/{%\s*(.*?)\s*%}/g);
        let parsedLine = line;
        if (variables) {
			for (const variable of variables) {
                const stringObject = variable.match(/^{%\s*(.*?)\s*%}$/)[1];
				parsedLine = parsedLine.replace(variable, Object.byString(variableStore, stringObject));
			}
        }
        for (const elem of document.getElementsByClassName('instruction_text')) {
            elem.innerHTML += " " + parsedLine;
        }
    }

    Object.byString = function(o, s) {
        s = s.replace(/\[(\w+)\]/g, '.$1'); // convert indexes to properties
        s = s.replace(/^\./, '');           // strip a leading dot
        var a = s.split('.');
        for (var i = 0, n = a.length; i < n; ++i) {
            var k = a[i];
            if (k in o) {
                o = o[k];
            } else {
                return;
            }
        }
        return o;
    }

    // Parse keyword line and return the match, keyword, and the command.
    function parseKeyWord(line) {
        return line.match(keyWordRegex);
    }

    function handleKeyWord(keyWord, command) {
        switch (keyWord) {
            case "show":
                document.getElementById(command).classList.remove("hidden");
                break;
            case "hide":
                document.getElementById(command).classList.add("hidden");
                break;
            case "makeVisible":
                document.getElementById(command).classList.remove("invisible");
                break;
            case "makeInvisible":
                document.getElementById(command).classList.add("invisible");
                break;
            case "page":
                currentPageTitle = command;
                break;
            case "header":
                for (const elem of document.getElementsByClassName("instruction_header")) {
                    elem.innerHTML = command;
                }
                break;
            case "set":
                parseSetCommand(command);
                break;
            case "event":
                parseEventCommand(command);
                break;
            case "waitFor":
                if (currentPage > lastCompletedPage) {
                    disableNextButtons();
                }
                parseListener(command);
                break;
            default:
                break;
        }
        return keyWord;
    }

    function parseListener(listener) {
        switch(listener) {
            case 'insuranceCheck':
                document.querySelector('#insurance-container .checkbox-container').addEventListener('change', userCheckedInsurance);
                break;
            case 'joySpending':
                client.investmentControl.slider_.addEnjoymentListener(joyChanged);
                break;
            case 'preventionSpending':
                client.investmentControl.slider_.addFitnessListener(fitnessChanged);
                break;
            case 'barDrag':
                const bar = document.querySelector('#slider .noUi-connect.enjoyment-color');
                bar.addEventListener('mousedown', barSlideMouseDown);
                bar.addEventListener('mouseup', barSlideMouseUp);
                client.investmentControl.slider_.addFitnessListener(barSlideFitnessChanged);
                break;
            case 'chatMessage':
                const msgBar = document.getElementById('chat-message');
                msgBar.addEventListener('keypress', chatMessageKeyPress);
                msgBar.addEventListener('input', chatMessageInput);
                break;
            case 'historyReview':
                setupHistoryReview();
                break;
            default:
                break;
        }
    }

    const histReviewChecks = { shockProb: false, prevention: false, enjoyment: false };
    function setupHistoryReview() {
        document.getElementById('shockProb-tab').addEventListener('click', shockProbTabClick);
        document.getElementById('prevention-tab').addEventListener('click', preventionTabClick);
        document.getElementById('enjoyment-tab').addEventListener('click', enjoymentTabClick);
    }

    function shockProbTabClick() {
        histReviewChecks.shockProb = true;
        historyReviewComplete();
    }

    function preventionTabClick() {
        histReviewChecks.prevention = true;
        historyReviewComplete();
    }

    function enjoymentTabClick() {
        histReviewChecks.enjoyment = true;
        historyReviewComplete();
    }

    function historyReviewComplete() {
        let isComplete = histReviewChecks.shockProb && histReviewChecks.prevention && histReviewChecks.enjoyment;
        if (isComplete) {
            enableNextButtons();
            document.getElementById('shockProb-tab').removeEventListener('click', shockProbTabClick);
            document.getElementById('prevention-tab').removeEventListener('click', preventionTabClick);
            document.getElementById('enjoyment-tab').removeEventListener('click', enjoymentTabClick);
        }
    }

    function chatMessageKeyPress(e) {
        if (e.keyCode == 13 && e.currentTarget.value.replace(/\s/g,"") !== "") {
            autoExpand(e.target);
            const msgBox = document.getElementById('chat-message');
            handleChatMessages(createChatMessages(msgBox.value));
            msgBox.value = "";
            chatMessageComplete();
            e.preventDefault();
        } else if (e.currentTarget.value.length >= 140 || e.keyCode == 13) {
            e.preventDefault();
        }
    }

    function chatMessageComplete() {
        enableNextButtons();
        const msgBar = document.getElementById('chat-message');
        msgBar.removeEventListener('keypress', chatMessageKeyPress);
        msgBar.removeEventListener('input', chatMessageInput);
    }

    function createChatMessages(message){
        const messages = [
            {
                name: client.statusController.myStatus.displayName,
                message: message
            }
        ];

        for (const otherStatus of client.statusController.initOtherStatus) {
            if (otherStatus.displayname === client.statusController.myStatus.displayName) {
                continue;
            }
            messages.push({
                name: otherStatus.displayname,
                message: "Responds to your message"
            });
        }
        
        return messages;
    }
    
    function handleChatMessages(messages){
        const messageList = $("#chat-messages");
        $.each(messages, function(i,msg){
            let name = msg.name;
			if (client.statusController.myStatus.displayName.toLowerCase() == name.toLowerCase()){
                name = expParams.translate("You");
            } else {
                name = expParams.translate("colors." + name);
            }
				
			
            messageList.append("<div class='chatmsg'><div class='chat-name " + msg.name.toLowerCase() + "'>" + name + ":</div>" + msg.message.replace(/['"]+/g, '') + "</div>");
        });

        messageList.animate({scrollTop: messageList[0].scrollHeight});
    }
    
    function autoExpand(field) {
        // Reset field height
        field.style.height = '2em';
    
        // Get the computed styles for the element
        var computed = window.getComputedStyle(field);
    
        // Calculate the height
        var height = parseInt(computed.getPropertyValue('border-top-width'), 10)
                        + parseInt(computed.getPropertyValue('padding-top'), 10)
                        + field.scrollHeight
                        + parseInt(computed.getPropertyValue('padding-bottom'), 10)
                        + parseInt(computed.getPropertyValue('border-bottom-width'), 10);
    
        field.style.height = height + 'px';
    }

    function chatMessageInput(e) {
        autoExpand(e.target);
    }

    let barSlideHolding = false;

    function barSlideMouseDown() {
        barSlideHolding = true;
    }

    function barSlideMouseUp() {
        barSlideHolding = false;
    }

    function barSlideFitnessChanged(value) {
        if (barSlideHolding) {
            barSlideComplete();
        }
    }

    function barSlideComplete() {
        enableNextButtons();
        const bar = document.querySelector('#slider .noUi-connect.enjoyment-color');
        bar.removeEventListener('mousedown', barSlideMouseDown);
        bar.removeEventListener('mouseup', barSlideMouseUp);
        client.investmentControl.slider_.removeFitnessListener(barSlideFitnessChanged);
    }

    function joyChanged(value) {
        enableNextButtons();
        client.investmentControl.slider_.removeEnjoymentListener(joyChanged);
    }

    function fitnessChanged(value) {
        enableNextButtons();
        client.investmentControl.slider_.removeFitnessListener(fitnessChanged);
    }

    function userCheckedInsurance() {
        enableNextButtons();
        document.querySelector('#insurance-container .checkbox-container').removeEventListener('change', userCheckedInsurance);
    }

    function enableNextButtons() {
        for (const elem of document.getElementsByClassName('next-button')) {
            elem.disabled = false;
        }
    }

    function disableNextButtons() {
        for (const elem of document.getElementsByClassName('next-button')) {
            elem.disabled = true;
        }
    }

    function parseSetCommand(command) {
        const [match, name, value] = command.match(/\s*(.*?)\s*=\s*(.*[^\s])\s*/);
        //variableStore[name] = value;

        // if this is just a number then we do not need to evaluate it.
        // if (/^(\s*|\d+\.?\d*|\.\d+)$/.test(value)) {
        //     variableStore[name] = value;
        // } else { // this is actually a variable and needs to be evaluated
        //     variableStore[name] = Object.byString(variableStore, value);
        // }
        variableStore[name] = parseStringCommand(value);
    }

    function parseStringCommand(command) {
        if (isFunctionRegex.test(command)) {
            return parseStringFunction(command);
        } else {
            return parseStringVariable(command);
            // if (isStringOrNumberRegex.test(command)) {
            //     return command;
            // } else {
            //     return Object.byString(variableStore, command);
            // }
        }
    }

    function parseStringVariable(stringVar) {
        const varValue = Object.byString(variableStore, stringVar);
        if (varValue) {
            return varValue;
        } else {
            return stringVar;
        }
    }

    function parseStringFunction(command) {
        const parameterString = command.match(/\b[^()]+\((.*)\)/)[1];
        const parameters = parameterString.split(',').map(p => p.trim());
        let newParameterString = "";
        for (const param of parameters) {
            if (newParameterString.length > 0) {
                newParameterString += ",";
            }

            newParameterString += parseStringCommand(param);
        }

        let eventString = command.replace(parameterString, newParameterString);
        if (eventString.includes('=')) {
            const [variable, event] = eventString.split('=').map(p => p.trim());
            parseSetCommand(variable + " = " + eval(event));
        } else {
            return eval(eventString);
        }
    }

    function parseEventCommand(command) {
        const parameterString = command.match(/\b[^()]+\((.*)\)/)[1];
        const parameters = parameterString.split(',').map(p => p.trim());
        let newParameterString = "";
        for (const param of parameters) {
            if (newParameterString.length > 0) {
                newParameterString += ",";
            }

            // if this is just a number then we do not need to evaluate it.
            if (/^(\s*|\d+\.?\d*|\.\d+)$/.test(param)) {
                newParameterString += param;
            } else { // this is actually a variable and needs to be evaluated
                newParameterString += Object.byString(variableStore, param);
            }
        }

        let eventString = command.replace(parameterString, newParameterString);
        if (eventString.includes('=')) {
            const [variable, event] = eventString.split('=').map(p => p.trim());
            parseSetCommand(variable + " = " + eval(event));
        } else {
            eval(eventString);
        }
    }

    function isKeyWord(line) {
        return keyWordRegex.test(line);
    }

    function loadInstruction() {
        pageSetup[currentPage - 1]();
        $.post("instruction_client/update_page", 
            {
                currentPage: currentPage, 
                complete: lastCompletedPage == lastPage
            }
        );
    }

    function nextPage() {
        if (currentPage >= lastPage) {
            return;
        }
        if (currentPage > lastCompletedPage) {
            lastCompletedPage = currentPage;
        }
        currentPage++;
        setupNextPage();
    }

    function previousPage() {
        if (currentPage <= 1) {
            curruentPage = 1;
            return;
        }
        currentPage--;
        enableNextButtons();
        findPreviousPage();
        setupNextPage();
    }

    function setStage(title) {
        updateElementText(document.getElementById('stage'), title);
    }

    /*
     * Instruction even methods
    */

    function getOtherPlayerCount() {
        return client.statusController.initOtherStatus.length - 1;
    }

    function setInvestmentStage() {
        setStage(expParams.translate("stages.Spending"));
    }

    function startShockDraw() {
        const shock = { 
			shockSize: expParams.playerType.shock.countSize, 
			shockCost: expParams.playerType.shock.incomeSize, 
			shocked: true, 
			prevented: false,
			draw: 1,
        };
        
        client.projectedWheel.spin(shock, () => {
			setStage(expParams.translate("shock_received_message"));
            client.statusController.updateStatus({ shocked: true, shocks: 1 });
            client.onShocksUpdated();
		});
    }

    function toPercent(decimal) {
        return decimal * 100;
    }

    function startLife() {
        createExampleState();
        client = new Client(expParams, otherStatus);
        variableStore["client"] = client;
        client.startLife(1);
    }

    function startInvestment() {
        client.statusController.updateStatus({budget: 30});
        client.investmentControl.reset();
        client.startInvestment();
    }

    function startInvestmentWithDebt() {
        prevInvestmentState = {};

        Object.assign(prevInvestmentState, client.investmentControl.decisions);
        client.statusController.updateStatus({budget: -200});
        client.startInvestment();
        client.statusController.updateStatus({budget: 30}, false);
    }

    function resumeInvestmentState() {
        //client.statusController.updateStatus(prevInvestmentState);
        if (prevInvestmentState) {
            client.statusController.updateStatus(client.statusController.myStatus);
            client.startInvestment(prevInvestmentState);
        }
    }

    function getIncomeText() {
        if (expParams.playerType.job.type === expParams.playerType.job.types.ageLinear && expParams.playerType.job.slope !== 0) {
            const slope = expParams.playerType.job.slope;
            return "a base <span class='font-weight-bold'>Income</span> of <span class='negative'>" + (expParams.playerType.job.intercept + slope) + "</span> and an additional income of <span class='negative'>" + slope + "</span> each additional period"
        } else {
            return "<span class='negative'>" + expParams.playerType.job.intercept + "</span> in <span class='font-weight-bold'>Income</span> every period";
        }
    }

    function add(a, b) {
        return a + b;
    }

    function difference(a, b) {
        return a - b;
    }
})(jQuery);