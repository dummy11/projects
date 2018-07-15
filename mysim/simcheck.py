import re

class simcheck(object):
    uvmErrorPattern = r'^.*UVM_((ERROR)|(FATAL)) .*\@.*:'
    vcsErrorPattern = r'^Error-\[.*\]'
    uvmWarningPattern = r'^.*UVM_WARNING .*\@.*:'
    uvmReportPattern = r'^--- UVM Report Summary ---'
    coreDumpPattern = r'Completed context dump phase'
    simEndPattern = r'V C S   S i m u l a t i o n   R e p o r t'
    ErrorTaskPattern = r'^Error.+:'
    timingViolationPattern = r'.*Timing violation.*'


    def __init__(self):
        super(simcheck,self).__init__()
        self._errPatterns = []
        self._excludeErrPatterns = []
        self.setErrPatterns(simcheck.uvmErrorPattern)
        self.setErrPatterns(simcheck.vcsErrorPattern)
        self.setErrPatterns(simcheck.coreDumpPattern)
        self.setErrPatterns(simcheck.ErrorTaskPattern)
        self._warnPatterns = []
        self._excludeWarnPatterns = []
        self.setWarnPatterns(simcheck.uvmWarningPattern)
        self.setWarnPatterns(simcheck.timingViolationPattern)
        self._endFlagPatterns = []
        self.setEndFlagPatterns(simcheck.uvmReportPattern)
        self.failStatus = ''
        self._reasonMsg = ''
        self._endFlagHit = False
        self._simEndPattern = re.compile(simcheck.simEndPattern)

    @property
    def status(self):
        if self._failStatus:
            return self._failStatus, self._reasonMsg
        elif not self._endFlagHit:
            self._failStatus = 'UNKNOWN'
            self._reasonMsg = 'No Simulation End Flag'
            return self._failStatus, self._reasonMsg
        else:
            return 'PASS',''


    def setErrPatterns(self, pattern):
        self._errPatterns.append(re.compile(pattern))


    def setWarnPatterns(self, pattern):
        self._warnPatterns.append(re.compile(pattern))

    def setExcludeErrPatterns(self, pattern):
        self._excludeErrPatterns.append(re.compile(pattern))


    def setExcludeWarnPatterns(self, pattern):
        self._excludeWarnPatterns.append(re.compile(pattern))


    def setEndFlagPatterns(self, pattern):
        self._endFlagPatterns.append(re.compile(pattern))

    def check(self, string):
        for errPattern in self._errPatterns:
            if errPattern.match(string):
                excluded = list(filter(lambda x:x.match(string), self._excludeErrPatterns))
                if not excluded:
                    if self._failStatus != 'FAIL':
                        self._failStatus = 'FAIL'
                        self._reasonMsg = string

        for warPattern in self._warnPatterns:
            if warnPattern.match(string):
                excluded = list(filter(lambda x:x.match(string), self._excludeWarnPatterns))
                if not excluded:
                    if not self._failStatus:
                        self._failStatus = 'WARN'
                        self._reasonMsg = string

        for endFlagPattern in self._endFlagPatterns:
            if endFlagPattern.match(string):
                self._endFlagHit = True

        if self._simEndPattern.match(string):
            return True

