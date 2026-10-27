import json
import math
import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Dict, Callable, Any, Set
 
random.seed(7)  #수업 결과 재현 위한 난수 시드 고정
 
def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))
 
def line():
    print('-' * 72)
 
print('✅ [모듈 1] 라이브러리 로드 완료')
