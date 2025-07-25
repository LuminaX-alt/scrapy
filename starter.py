#engine-lifecycle-state-machine.patch
diff --git a/scrapy/core/engine.py b/scrapy/core/engine.py
index 8d7d0b3..f45b9aa 100644
--- a/scrapy/core/engine.py
+++ b/scrapy/core/engine.py
@@ -33,6 +33,15 @@ from twisted.internet import defer, task
 from twisted.python import failure
 from scrapy.utils.log import failure_to_exc_info
 from scrapy.utils.reactor import CallLaterOnce
+
+from enum import Enum, auto
+import logging
+
+logger = logging.getLogger(__name__)
+
+class EngineState(Enum):
+    IDLE = auto()
+    STARTING = auto()
+    RUNNING = auto()
+    STOPPING = auto()
+    STOPPED = auto()
 
 class ExecutionEngine:
 
     def __init__(self, crawler, spider_closed_callback):
         self.crawler = crawler
         self.spider_closed_callback = spider_closed_callback
@@ -112,6 +121,8 @@ class ExecutionEngine:
         self._scraper = Scraper(crawler)
         self._check_shutdown = CallLaterOnce(self._maybe_shutdown)
         self._running = False
+        # Track engine lifecycle state
+        self._state = EngineState.IDLE
@@ -178,8 +189,15 @@ class ExecutionEngine:
     @defer.inlineCallbacks
     def start_async(self):
-        self._running = True
-        yield self.open_spider(self.spider)
+        if self._state not in (EngineState.IDLE, EngineState.STOPPED):
+            logger.warning("start_async() called in invalid state: %s", self._state)
+            return
+        self._set_state(EngineState.STARTING)
+        self._running = True
+        try:
+            yield self.open_spider(self.spider)
+            self._set_state(EngineState.RUNNING)
+        except Exception as e:
+            logger.exception("Error during start_async: %s", e)
+            yield self.stop()
+            raise
@@ -270,6 +288,10 @@ class ExecutionEngine:
     @defer.inlineCallbacks
     def open_spider(self, spider, start_requests=None):
+        if self._state in (EngineState.STOPPING, EngineState.STOPPED):
+            logger.warning("open_spider() skipped: Engine stopping/stopped.")
+            return
+
         self.signals.send_catch_log_deferred(
             signal=signals.spider_opened, spider=spider
         )
@@ -360,7 +382,13 @@ class ExecutionEngine:
     @defer.inlineCallbacks
     def stop(self):
-        yield self.close()
+        if self._state in (EngineState.STOPPING, EngineState.STOPPED):
+            logger.debug("stop() called but engine already stopping/stopped.")
+            return
+        self._set_state(EngineState.STOPPING)
+        try:
+            yield self.close()
+        finally:
+            self._set_state(EngineState.STOPPED)
@@ -420,6 +448,10 @@ class ExecutionEngine:
     @defer.inlineCallbacks
     def close_spider(self, spider, reason='cancelled'):
+        if self._state == EngineState.STOPPED:
+            logger.debug("close_spider() ignored: Engine already stopped.")
+            return
+
         self.signals.send_catch_log_deferred(
             signal=signals.spider_closed, spider=spider, reason=reason
         )
+
+    def _set_state(self, new_state: EngineState):
+        logger.debug("Engine state transition: %s -> %s", self._state, new_state)
+        self._state = new_state
#engine-lifecycle-state-machine.patch
