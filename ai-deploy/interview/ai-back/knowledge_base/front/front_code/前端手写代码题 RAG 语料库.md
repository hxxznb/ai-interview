## ## 手写实现数组扁平化 (flat)

**考察重点：** 递归思想、数组方法综合运用

**解题思路：**

1. 遍历数组每一项，判断当前元素是否是数组
2. 如果是数组，递归调用自身继续展开
3. 如果不是数组，直接推入结果数组
4. 可以通过传入 depth 参数控制展开层数

**关键代码：**

```javascript
// 方法一：递归实现
function flatten(arr, depth = Infinity) {
  const result = [];
  for (const item of arr) {
    if (Array.isArray(item) && depth > 0) {
      result.push(...flatten(item, depth - 1));
    } else {
      result.push(item);
    }
  }
  return result;
}

// 方法二：reduce 实现
function flattenReduce(arr) {
  return arr.reduce((acc, cur) => {
    return acc.concat(Array.isArray(cur) ? flattenReduce(cur) : cur);
  }, []);
}

// 测试
console.log(flatten([1, [2, [3, [4]]]])); // [1, 2, 3, 4]
```

## ## 手写实现防抖函数 (debounce)

**考察重点：** 闭包、定时器、this 指向

**解题思路：**

1. 核心原理：事件触发后延迟 n 秒执行，如果 n 秒内再次触发则重新计时
2. 利用闭包保存定时器 ID
3. 每次调用先清除上一次的定时器，再开启新定时器
4. 注意 this 指向和参数透传

**关键代码：**

```javascript
function debounce(fn, delay = 300, immediate = false) {
  let timer = null;
  return function (...args) {
    // 是否需要立即执行（首次触发立刻执行，后续等待）
    if (immediate && !timer) {
      fn.apply(this, args);
    }
    clearTimeout(timer);
    timer = setTimeout(() => {
      if (!immediate) {
        fn.apply(this, args);
      }
      timer = null;
    }, delay);
  };
}

// 使用示例
const handleInput = debounce((e) => {
  console.log('搜索:', e.target.value);
}, 500);
```

## ## 手写实现节流函数 (throttle)

**考察重点：** 闭包、时间戳/定时器两种方案

**解题思路：**

1. 核心原理：在连续触发事件时，保证 n 秒内只执行一次
2. 时间戳方案：记录上次执行时间，当前时间与上次间隔超过 delay 才执行
3. 定时器方案：如果定时器不存在，设置定时器，执行后清空

**关键代码：**

```javascript
// 时间戳方案（首次立即执行，停止触发后不会再执行）
function throttle(fn, delay = 300) {
  let lastTime = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastTime >= delay) {
      fn.apply(this, args);
      lastTime = now;
    }
  };
}

// 定时器方案（首次不立即执行，停止触发后还会执行一次）
function throttleTimer(fn, delay = 300) {
  let timer = null;
  return function (...args) {
    if (!timer) {
      timer = setTimeout(() => {
        fn.apply(this, args);
        timer = null;
      }, delay);
    }
  };
}
```

## ## 手写实现深拷贝 (deepClone)

**考察重点：** 递归、类型判断、循环引用处理

**解题思路：**

1. 判断传入值的类型：基本类型直接返回
2. 处理特殊对象：Date 返回新 Date，RegExp 返回新 RegExp
3. 使用 WeakMap 记录已拷贝的对象，解决循环引用问题
4. 递归拷贝对象的每个属性

**关键代码：**

```javascript
function deepClone(obj, map = new WeakMap()) {
  // 基本类型直接返回
  if (obj === null || typeof obj !== 'object') return obj;

  // 处理特殊对象
  if (obj instanceof Date) return new Date(obj);
  if (obj instanceof RegExp) return new RegExp(obj);

  // 解决循环引用：如果已经拷贝过，直接返回
  if (map.has(obj)) return map.get(obj);

  // 创建同类型容器
  const clone = Array.isArray(obj) ? [] : {};
  map.set(obj, clone);

  // 递归拷贝所有属性（包括 Symbol 类型的 key）
  Reflect.ownKeys(obj).forEach(key => {
    clone[key] = deepClone(obj[key], map);
  });

  return clone;
}

// 测试循环引用
const a = { name: 'test' };
a.self = a;
console.log(deepClone(a)); // 正常输出，不会栈溢出
```

## ## 手写实现 Promise.all

**考察重点：** Promise 机制、异步并发控制

**解题思路：**

1. 接收一个可迭代对象（通常是 Promise 数组）
2. 返回一个新的 Promise
3. 所有 Promise 都 resolve 后，按原始顺序返回结果数组
4. 任何一个 reject 则立即 reject
5. 用计数器而非 results.length 判断完成（因为异步顺序不确定）

**关键代码：**

```javascript
function myPromiseAll(promises) {
  return new Promise((resolve, reject) => {
    const results = [];
    let count = 0;
    const promiseArr = Array.from(promises);

    if (promiseArr.length === 0) {
      return resolve([]);
    }

    promiseArr.forEach((p, index) => {
      // 用 Promise.resolve 包裹，兼容非 Promise 值
      Promise.resolve(p).then(
        (value) => {
          results[index] = value; // 用 index 保持顺序
          count++;
          if (count === promiseArr.length) {
            resolve(results);
          }
        },
        (reason) => {
          reject(reason); // 任何一个失败直接 reject
        }
      );
    });
  });
}
```

## ## 手写实现 call / apply / bind

**考察重点：** this 绑定原理、函数作为对象方法调用时 this 指向调用者

**解题思路：**

1. call/apply 核心：将函数设为目标对象的临时方法，调用后删除
2. bind 核心：返回一个新函数，内部用 apply 绑定 this
3. bind 需要处理 new 调用的情况（new 的优先级高于 bind）

**关键代码：**

```javascript
// 手写 call
Function.prototype.myCall = function (context = window, ...args) {
  const key = Symbol('temp'); // 用 Symbol 避免属性冲突
  context[key] = this;        // this 就是调用 myCall 的那个函数
  const result = context[key](...args);
  delete context[key];
  return result;
};

// 手写 apply（与 call 唯一区别：参数是数组）
Function.prototype.myApply = function (context = window, args = []) {
  const key = Symbol('temp');
  context[key] = this;
  const result = context[key](...args);
  delete context[key];
  return result;
};

// 手写 bind
Function.prototype.myBind = function (context, ...outerArgs) {
  const fn = this;
  return function BoundFn(...innerArgs) {
    // 如果是通过 new 调用，this 指向新创建的实例
    if (this instanceof BoundFn) {
      return new fn(...outerArgs, ...innerArgs);
    }
    return fn.apply(context, [...outerArgs, ...innerArgs]);
  };
};
```

## ## 手写实现 new 操作符

**考察重点：** 原型链、构造函数、对象创建过程

**解题思路：**
new 操作符内部做了四件事：

1. 创建一个空对象
2. 将空对象的原型链 __proto__ 指向构造函数的 prototype
3. 将构造函数的 this 绑定到新对象并执行
4. 如果构造函数返回对象则用该对象，否则返回新建的对象

**关键代码：**

```javascript
function myNew(Constructor, ...args) {
  // 1. 创建空对象，原型指向构造函数的 prototype
  const obj = Object.create(Constructor.prototype);
  // 2. 执行构造函数，this 绑定到 obj
  const result = Constructor.apply(obj, args);
  // 3. 如果构造函数返回了一个对象，则用它；否则返回 obj
  return result instanceof Object ? result : obj;
}

// 测试
function Person(name, age) {
  this.name = name;
  this.age = age;
}
const p = myNew(Person, '张三', 25);
console.log(p.name); // 张三
console.log(p instanceof Person); // true
```

## ## 手写实现 EventEmitter（发布-订阅模式）

**考察重点：** 设计模式、Map/数组操作

**解题思路：**

1. 维护一个事件名到回调函数数组的映射表
2. on：注册事件监听器
3. once：注册只触发一次的监听器（触发后自动移除）
4. emit：触发事件，执行所有对应的回调
5. off：移除指定的事件监听器

**关键代码：**

```javascript
class EventEmitter {
  constructor() {
    this.events = new Map();
  }

  on(event, callback) {
    if (!this.events.has(event)) {
      this.events.set(event, []);
    }
    this.events.get(event).push(callback);
    return this; // 支持链式调用
  }

  once(event, callback) {
    const wrapper = (...args) => {
      callback.apply(this, args);
      this.off(event, wrapper);
    };
    this.on(event, wrapper);
    return this;
  }

  emit(event, ...args) {
    if (this.events.has(event)) {
      this.events.get(event).forEach(cb => cb.apply(this, args));
    }
    return this;
  }

  off(event, callback) {
    if (this.events.has(event)) {
      const cbs = this.events.get(event).filter(cb => cb !== callback);
      this.events.set(event, cbs);
    }
    return this;
  }
}
```

## ## 手写实现 instanceof 运算符

**考察重点：** 原型链查找机制

**解题思路：**

1. instanceof 的本质是沿着对象的原型链（__proto__）向上查找
2. 如果在原型链上找到了构造函数的 prototype，返回 true
3. 如果一直找到 null（原型链顶端）都没找到，返回 false

**关键代码：**

```javascript
function myInstanceof(obj, Constructor) {
  // 基本类型直接返回 false
  if (obj === null || (typeof obj !== 'object' && typeof obj !== 'function')) {
    return false;
  }

  let proto = Object.getPrototypeOf(obj);
  const target = Constructor.prototype;

  while (proto !== null) {
    if (proto === target) {
      return true;
    }
    proto = Object.getPrototypeOf(proto);
  }
  return false;
}

// 测试
console.log(myInstanceof([], Array));   // true
console.log(myInstanceof([], Object));  // true
console.log(myInstanceof('str', String)); // false（基本类型）
```

## ## 用 Promise 实现红绿灯交替循环

**考察重点：** Promise 链式调用、异步流程控制

**解题思路：**

1. 封装一个延时亮灯函数，返回 Promise
2. 绿灯 3 秒 → 黄灯 1 秒 → 红灯 2 秒 → 循环
3. 使用递归或 async/await 串联整个流程

**关键代码：**

```javascript
function light(color, duration) {
  return new Promise((resolve) => {
    console.log(`${color} 灯亮了`);
    setTimeout(resolve, duration);
  });
}

async function trafficLight() {
  while (true) {
    await light('🟢 绿', 3000);
    await light('🟡 黄', 1000);
    await light('🔴 红', 2000);
  }
}

trafficLight();
```

## ## 手写实现简易版 hooks (useState 实现原理)

**考察重点：** 闭包的应用、React 渲染关联

**解题思路：**

1. 内部维护一个 `state` 变量和 `setters` 数组
2. `useState` 被调用时，根据当前 `cursor` (下标) 返回对应的状态
3. `setState` 被调用时，更新对应的 `state` 并触发视图重新渲染
4. 注意：在真实 React 中，这是基于 Fiber 的单向链表实现的

**关键代码：**

```javascript
let state = []; // 存储状态
let setters = []; // 存储修改状态的函数
let cursor = 0; // 当前游标

function createSetter(index) {
  return function(newVal) {
    state[index] = newVal;
    render(); // 模拟触发组件渲染
  };
}

function myUseState(initialVal) {
  if (setters[cursor] === undefined) {
    state[cursor] = initialVal;
    setters[cursor] = createSetter(cursor);
  }

  const res = [state[cursor], setters[cursor]];
  cursor++; // 游标移向下一个
  return res;
}

function render() {
  cursor = 0; // 渲染前重置游标
  // ... 执行组件渲染逻辑
}
```

## ## 手写实现 useDebounce Hook

**考察重点：** React Hooks 复用、闭包与定时器

**解题思路：**

1. 创建一个新的状态 `debouncedValue`
2. 使用 `useEffect` 监听源 `value` 的变化
3. 在 `useEffect` 内部开启定时器，到期后更新 `debouncedValue`
4. 返回 `useEffect` 的清理函数来清除上一次的定时器

**关键代码：**

```javascript
import { useState, useEffect } from 'react';

function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // 清理函数：如果 value 或 delay 在 500ms 内变动，清除上一个定时器
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

## ## 手写实现 Redux 的 createStore

**考察重点：** 观察者模式、闭包隔离状态

**解题思路：**

1. 内部变量 `state` 存储当前状态，`listeners` 存储订阅回调
2. `getState`：直接返回当前 state
3. `subscribe`：收集回调，并返回一个取消订阅的函数
4. `dispatch`：接收 action，通过 reducer 计算新 state，并通知所有订阅者

**关键代码：**

```javascript
function createStore(reducer, initialState) {
  let state = initialState;
  let listeners = [];

  function getState() {
    return state;
  }

  function subscribe(listener) {
    listeners.push(listener);
    return () => {
      listeners = listeners.filter(l => l !== listener);
    };
  }

  function dispatch(action) {
    state = reducer(state, action);
    listeners.forEach(l => l());
  }

  // 初始化 dispatch 一次，获取初始 state
  dispatch({ type: '@@INIT' });

  return { getState, subscribe, dispatch };
}
```

## ## 手写实现 Promise.race

**考察重点：** Promise 状态只能变更一次特性、异步并发

**解题思路：**

1. 接收一个 Promise 数组。
2. 返回一个新的 Promise。
3. 遍历数组，只要其中任何一个 Promise 率先完成（resolve 或 reject），返回的新 Promise 立即同步该状态。

**关键代码：**

```javascript
function myPromiseRace(promises) {
  return new Promise((resolve, reject) => {
    for (const p of promises) {
      // 用 Promise.resolve 包裹，确保兼容非 Promise 值
      Promise.resolve(p).then(resolve, reject);
    }
  });
}
```

## ## 手写实现 Array.prototype.reduce

**考察重点：** 累加器思想、数组原型方法实现

**解题思路：**

1. 语法：`arr.reduce(callback(accumulator, currentValue, index, array), initialValue)`。
2. 如果未提供 `initialValue`，则以数组第一个元素作为初始值，从第二个元素开始迭代。
3. 否则，以 `initialValue` 作为初始值，从第一个元素开始迭代。

**关键代码：**

```javascript
Array.prototype.myReduce = function(callback, initialValue) {
  const arr = this;
  let accumulator = initialValue !== undefined ? initialValue : arr[0];
  let startIndex = initialValue !== undefined ? 0 : 1;

  for (let i = startIndex; i < arr.length; i++) {
    accumulator = callback(accumulator, arr[i], i, arr);
  }
  return accumulator;
};
```

## ## 手写实现深拷贝 (Deep Clone - 完善版)

**考察重点：** 递归逻辑、**处理循环引用**、类型判断

**解题思路：**

1. 使用 `WeakMap` 存储已经拷贝过的对象。
2. 每次拷贝前先检查 `WeakMap` 中是否存在，若存在直接返回，防止死循环（堆栈溢出）。
3. 递归处理数组和对象。

**关键代码：**

```javascript
function deepClone(obj, hash = new WeakMap()) {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj);
  if (obj instanceof RegExp) return new RegExp(obj);

  // 如果已经拷贝过，直接返回之前存储的对象
  if (hash.has(obj)) return hash.get(obj);

  const cloneObj = Array.isArray(obj) ? [] : {};
  hash.set(obj, cloneObj);

  for (let key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloneObj[key] = deepClone(obj[key], hash);
    }
  }
  return cloneObj;
}
```
