from datetime import timedelta, datetime
from aiogram.types import (
    CallbackQuery
)

from devtools import debug
from typing import Type
from dataclasses import dataclass, field
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton
)
from typing import Any

from models import Operation, Content
import locale

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

def align_kbd(kbd: list[InlineKeyboardButton], btn_in_row: int):
    kbd_ = []
    for row in range(0, len(kbd), btn_in_row):
        kbd_.append(kbd[row:row+btn_in_row])
    return kbd_
        
@dataclass
class DaySelect:
    start: int
    stop: int
    btn_in_row: int = field(default=3)
    _value: int = field(default=-1)

    def daterange(self,start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)
   
    async def content(self, op: Any = None) -> Content | None:                
        match op:
            case Operation.START:
                kbd = []                
                for i in self.daterange(self.start, self.stop+timedelta(days=1)):                                    
                    # i.strftime("%s") ts
                    kbd.append(InlineKeyboardButton(text=i.strftime("%a %d %b %y"), callback_data=i.strftime("%s")))        
                
                kbd = align_kbd(kbd, self.btn_in_row)
            case _:
                return Content(None, str(self._value))
        return Content(kbd)
    
    async def callback(self, callback_query: CallbackQuery) -> int | None:  

        try:
            
            self._value = int(callback_query.data)
    
            return self._value
        except ValueError:
            return None

@dataclass
class HourSelect:

    start: int
    stop: int | None
    next_day: bool = field(default=True)
    btn_in_row: int = field(default=6)
    _value: int = field(default=-1)    
    #parent: 

    async def content(self, op: Any = None) -> Content | None:                
        stop = 23 if self.stop is None else self.stop
        
        match op:
            case Operation.START:
                kbd = []                
                for i in range(self.start, stop+1):
                    kbd.append(InlineKeyboardButton(text=str(i), callback_data=str(i)))        
                if self.next_day and self.stop is None:                    
                    for i in range(0, 8):
                        
                        kbd.append(InlineKeyboardButton(text=str(i)+'+1d', callback_data=str(i+24)))        
                
                kbd = align_kbd(kbd, self.btn_in_row)
            case _:
                return Content(None, str(self._value))
        return Content(kbd)

    async def callback(self, callback_query: CallbackQuery) -> int | None:  

        try:            
            self._value = int(callback_query.data)
            return self._value
        except ValueError:
            return None
        
@dataclass
class MinSelect:    
    start_m: int
    stop_m: int
    step: int = field(default=30)
    btn_in_row: int = field(default=6)
    _value: int = field(default=-1)
    

    def __post_init__(self):
        if self.step < 2:
            raise NotImplementedError('Step can\'t be less than 2')
   
    async def content(self, op: Operation|None = None) -> Content | None:               
        match op:
            case Operation.START:
                kbd = []
                for i in range(self.start_m, self.stop_m+1, self.step):
                    kbd.append(InlineKeyboardButton(text=str(i), callback_data=str(i)))
                kbd = align_kbd(kbd, self.btn_in_row)
            case _:
                return Content(None, str(self._value))
        return Content(kbd)
    

    async def callback(self, callback_query: CallbackQuery) -> int | None:             
        try:
            self._value = int(callback_query.data)
            return self._value
        except ValueError:
            return None           

@dataclass
class TimeIntervalSelect:
    
    next_day: bool
    value: dict = field(default_factory=dict, kw_only=True)

    async def time_interval(self, dates_name_interval, hours_name_interval, minutes_name_interval):

        _value = {}
        _date =  self.value[dates_name_interval] if dates_name_interval == 'date_from' else datetime.fromtimestamp(self.value[dates_name_interval])
        _value = datetime(day=_date.day, month=_date.month, year=_date.year)
        
        if self.next_day and self.value[hours_name_interval] > 23:
            self.value[hours_name_interval] = self.value[hours_name_interval] - 24              
            _value = _value + timedelta(days=1)                                   
                        
        _value = _value+timedelta(hours=self.value[hours_name_interval], minutes=self.value[minutes_name_interval])
        return _value
        

@dataclass
class InputDate:

    start_from: datetime
    stop_from: datetime | None
   
    next_day: bool = field(default=True)
    minute_step: int = field(default=30)
    _child_classes_from: dict[str, Type[DaySelect]|Type[HourSelect]|Type[MinSelect]] = field(default_factory=lambda: {'date_1':DaySelect ,'hour_1': HourSelect, 'minute_1': MinSelect})
    _child_classes_to: dict[str, Type[HourSelect]|Type[MinSelect]] = field(default_factory=lambda: {'hour_2': HourSelect, 'minute_2':MinSelect})
    _childs: dict[str, DaySelect|HourSelect|MinSelect] = field(default_factory=dict)
    state: str = field(default='', kw_only=True)
    _value: dict = field(default_factory=dict, kw_only=True)

    # @property
    # def _value(self):
    #     return {'hour': self.hour._value, 'minute': self.minute._value} # Incorrect
    
    @property
    def _states(self):
        _child_classes = list(self._child_classes_from.keys())+list(self._child_classes_to.keys())
        return _child_classes

    @property
    def _next_state(self):
        idx = self._states.index(self.state) + 1
        if idx < len(self._states):
            return self._states[idx]
        return None

    @property
    def _prev_state(self):
        idx = self._states.index(self.state) - 1
        if idx > 0:
            return self._states[idx]
        return None
        
    async def _date(self,_child_classes, dates_name_interval: str, start: datetime, stop: datetime):
        if dates_name_interval not in self._childs.keys():
            day = _child_classes[dates_name_interval](start, stop)
            self._childs[dates_name_interval] = day
            op = Operation.START
        else:
            day = self._childs[dates_name_interval]
            day.start = start.day
            day.stop = stop.day
            op = Operation.NEXT

            # content = await day.content(op=op)
                
        return day, op

    async def _hour(self, _child_classes, hours_name_interval: str, start: datetime, stop: datetime, next_day):
        stop = None if stop.hour is None or stop.hour == 0 else stop.hour
            
        if hours_name_interval not in self._childs.keys():
            hour = _child_classes[hours_name_interval](start.hour, stop,  next_day)
            self._childs[hours_name_interval] = hour
            op = Operation.START
        else:
            hour = self._childs[hours_name_interval]
            hour.start = start.hour
            hour.stop = stop             
            op = Operation.NEXT   
                            
        return hour, op
    
    async def _minute(self, _child_classes, hours_name_interval: str, minutes_name_interval: str, start: datetime, stop: datetime, minute_step):
        _stop = None if stop.hour == 0 else stop.hour
        
        m_start = 0
        m_stop = 59
                
        hour_value = self._value.get(hours_name_interval)
        
        if hour_value is None:
            raise ValueError('No hour selected')
        if hour_value == start.hour:
            m_start = start.minute
        if hour_value == _stop:
            debug(stop.minute)
            m_stop = stop.minute
                    
        if minutes_name_interval not in self._childs.keys():
            _minute = _child_classes[minutes_name_interval](m_start, m_stop, minute_step)
            self._childs[minutes_name_interval] = _minute
            op = Operation.START
        else:
            _minute = self._childs[minutes_name_interval]
            _minute.start = m_start
            _minute.stop = stop.minute
            op = Operation.NEXT

                # content = await minute.content(op=op)
                # return content
        
        return _minute, op      

    async def content(self, op: Operation|None=None):         
        match op:
            case Operation.START:
                self.state = self._states[0]
            case Operation.NEXT:
                content = await self._childs[self.state].content(op)
                if content is None or content.kbd is None:
                    self.state = self._next_state
                else:
                    return content # Modify content
            case _:
                return Content(None, str(self._value))
            
        match self.state:

            case 'date_1':
                day, op = await self._date(self._child_classes_from,dates_name_interval='date_1',start=self.start_from, stop=self.stop_from)
                content = await day.content(op=op)
                return content                

            case 'hour_1':  
                hour, op = await self._hour(self._child_classes_from,hours_name_interval='hour_1',start=self.start_from, stop=self.stop_from, next_day=False)              
                content = await hour.content(op=op)
                return content                
            
            case 'minute_1':
                minute, op = await self._minute(self._child_classes_from,hours_name_interval='hour_1',minutes_name_interval='minute_1',start=self.start_from, stop=self.stop_from, minute_step=self.minute_step)
                content = await minute.content(op=op)
                return content                
            
            case 'hour_2':
                hour, op = await self._hour(self._child_classes_to,hours_name_interval='hour_2', start=self.start_from, stop=self.stop_from, next_day=self.next_day)
                content = await hour.content(op=op)
                return content

            case 'minute_2':
                minute, op = await self._minute(self._child_classes_to,hours_name_interval='hour_2', minutes_name_interval='minute_2', start=self.start_from, stop=self.stop_from, minute_step=self.minute_step)
                content = await minute.content(op=op)
                return content

            case _:
                return Content(None, str(self._value))
        
            
    async def callback(self, callback_query: CallbackQuery):
        
        result = await self._childs[self.state].callback(callback_query)
        if result is not None:

            self._value[self.state] = result
        else:        
            # Process self buttons
            ...
        
        # self._childs[self.state]._value = result
        
        value = TimeIntervalSelect(value=self._value, next_day=self.next_day)
        
        # if all([i in self._value.keys() for i in self._child_classes.keys()]): 
        #   # return time(*[self._value[i] for i in self._child_classes.keys()])             
        if all([i in self._value.keys() for i in self._child_classes_from.keys()]):            
                                
            self._value = {}
            self._value['date_from'] = await value.time_interval(dates_name_interval='date_1', hours_name_interval='hour_1', minutes_name_interval='minute_1')            
            self.start_from = self._value['date_from']            

        if all([i in self._value.keys() for i in self._child_classes_to.keys()]):
                                
            self._value = {}
            self._value['date_from'] = self.start_from
            self._value['date_to'] = await value.time_interval(dates_name_interval='date_from', hours_name_interval='hour_2', minutes_name_interval='minute_2')
                            
            # return [self._value.keys() for i in self._child_classes.keys()]
            return self._value
            # return timedelta(*[self._value[i] for i in self._child_classes.keys()])

        return self._value

