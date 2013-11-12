Tamarradio
==========

Sorry, this readme is mostly italian by now. Someday we'll translate it.


Features
---------

There are a lot of radio schedulers out there; we aimed to write one that:
* Allows different kind of actions and alarms
* Allows events to be handled intelligently: they can wait for the current
  song to finish, or break in the middle, as you prefer
* Allows to change (interactively or programmatically) the way with which
  events are handled. For example, we want to completely _disable_ events sometimes.
* Aggressively caches files; this make network storage much more reliable
* is headless, but has many ways to connect: tcp commands, HTTP API, WebUI for
  the DB

Entita'
----------

* **traccia**: brano musicale in genere (tutto deve essere locale)
* **playlist**: raccolte di tracce. Queste playlist sono generate ad hoc (specificando i files che devono includere) oppure in maniera automatica (i file contenuti in una directory) - questo richiede un controllo (inotify) sul fs.
Esiste una playlist di default che e' la bobina.
* **specifica-tempo**: puo' essere una tantum, frequenza a minuti, oppure per certi giorni della settimana a un certo orario. (es: lunedi e venerdi alle 22.00).
* **azione**: e' una regola che genera una playlist da suonare. Tipicamente prende un file in modo "statico" e lo suona, oppure prende dal controller una raccolta e ne seleziona alcune tracce. In ogni caso un'azione NON controlla il flusso  direttamente!
* **evento**: <specifica-tempo, azione>
* **GestoreEventi** : questa entita', sulla base degli eventi che sono stati caricati (rilevati all'avvio nello storage o sottomessi durante l'esecuzione del tutto) dice quali evento far suonare nel momento in cui gli viene richiesta questa domanda. Nel mento in cui l'utente DISABILITA gli eventi, il GestoreEventi prende i contenuti da suonare unicamente dalla playlist di default, scartando qualsiasi altra playlist definita.
* **Player**: suona

Logica
----------

Questa potrebbe essere la logica generica. Non comprende funzioni specifiche (esempio: se arriva un'evento blocca la canzone attuale). In linea di massima pero', dovrebbe essere qualcosa del genere.

	qualcosaDaSuonare = qualcosa // INIZIA PRENDENDO QUALCOSA DALLA BOBINA
	While (true) { // CICLO INFINITO
		suonaqualcosa( qualcosaDaSuonare ) // SUONA FINO A CHE NON FINISCE
		qualcosaDaSuonare = GestoreEventi.getNextEvent() // CAPISCI COSA SUONARE DOPO 
	}

Comandi remoti 
----------
Questi i comandi che l'interfaccia deve poter comunicare al controller

* stopevents() ferma la schedulazione degli eventi (suonando solamente la playlist di default - bobina)
* startvents() avvia la schedulazione degli eventi 
* info() prende le info su cosa sta suonando ora
* newplaylist() ??? questo comando va implementato?

Struttura directory
----------

	/root/musica #raccolta di default dell'automatico ("bobina")
	/root/playlists #radice di tutte le altre playlist ("raccolte specifiche")
	/root/playlists/spot
	/root/playlists/jingle
	/root/playlists/jazz
	/root/playlists/blues
	/root/playlists/....

WebUI, DB e altri appunti
--------------------------

### Organizzazione

Tra player e webui la parte in comune e' il db, che quindi deve essere un package a parte: tamarradb.
Questo definisce fondamentalmente gli eventi, dividendo pero' per benino tutti i "sottotipi" di azione e di alarm.

### Web

No authentication is performed
L'interfaccia web consiste essenzialmente in un CRUD sugli eventi, ma deve gestire i sottotipi.

Proposta:
* form unico che usando javascript "nasconde" le parti non usate
* in fase di modifica, imporre che non si puo' cambiare il tipo (semplice variabile che in js disabilita la scelta). Questo semplifica l'implementazione della modifica

Cose da capire:
* sarebbe buono poter fare form composto da sottoform. ad esempio si potrebbe avere un EventForm formato da AlarmForm + ActionForm. Magari si potrebbero anche dividere i Form di allarmi ed azioni per ogni sottotipo, ma non e' necessarissimo.

Testing
=========

Just use `nosetests` to collect and run every test

