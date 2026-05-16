## ## 手写实现单例模式（双重检查锁 DCL）

**考察重点：** 设计模式、volatile、synchronized、线程安全

**解题思路：**

1. 私有化构造方法，防止外部 new
2. 双重检查锁（Double-Checked Locking）：先检查实例是否为空（避免不必要的加锁），再在 synchronized 块内二次检查
3. 用 volatile 修饰实例变量，防止指令重排序导致的半初始化对象问题
4. 外层 if 提升性能，内层 if 保证线程安全

**关键代码：**

```java
public class Singleton {
    // volatile 禁止指令重排序，防止分配内存但未初始化就被其他线程获取
    private static volatile Singleton instance;

    // 私有构造方法
    private Singleton() {}

    public static Singleton getInstance() {
        if (instance == null) {           // 第一次检查（无锁，提升性能）
            synchronized (Singleton.class) {
                if (instance == null) {   // 第二次检查（加锁后确保唯一）
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

## ## 手写实现生产者-消费者模式

**考察重点：** 多线程同步、wait/notify 机制、阻塞队列思想

**解题思路：**

1. 共享一个有界缓冲区（如 LinkedList 模拟队列）
2. 生产者：缓冲区满时 wait()，生产后 notifyAll() 唤醒消费者
3. 消费者：缓冲区空时 wait()，消费后 notifyAll() 唤醒生产者
4. 必须在 synchronized 块内调用 wait/notify

**关键代码：**

```java
import java.util.LinkedList;
import java.util.Queue;

public class ProducerConsumer {
    private static final int MAX_SIZE = 5;
    private static final Queue<Integer> queue = new LinkedList<>();

    public static void main(String[] args) {
        Object lock = new Object();

        // 生产者线程
        Thread producer = new Thread(() -> {
            int value = 0;
            while (true) {
                synchronized (lock) {
                    while (queue.size() == MAX_SIZE) {
                        try { lock.wait(); } catch (InterruptedException e) { break; }
                    }
                    queue.offer(value);
                    System.out.println("生产: " + value++);
                    lock.notifyAll();
                }
            }
        });

        // 消费者线程
        Thread consumer = new Thread(() -> {
            while (true) {
                synchronized (lock) {
                    while (queue.isEmpty()) {
                        try { lock.wait(); } catch (InterruptedException e) { break; }
                    }
                    int val = queue.poll();
                    System.out.println("消费: " + val);
                    lock.notifyAll();
                }
            }
        });

        producer.start();
        consumer.start();
    }
}
```

## ## 手写实现 LRU 缓存（Least Recently Used）

**考察重点：** 数据结构设计、HashMap + 双向链表组合

**解题思路：**

1. 使用 HashMap 实现 O(1) 的查找
2. 使用双向链表维护访问顺序（最新在头部，最久在尾部）
3. get 操作：查到后将节点移到头部
4. put 操作：新增节点放头部；若超过容量则淘汰尾部节点
5. Java 也可以直接继承 LinkedHashMap 实现

**关键代码：**

```java
import java.util.HashMap;
import java.util.Map;

public class LRUCache {
    // 双向链表节点
    static class Node {
        int key, value;
        Node prev, next;
        Node(int key, int value) { this.key = key; this.value = value; }
    }

    private final int capacity;
    private final Map<Integer, Node> map;
    private final Node head, tail; // 哨兵节点

    public LRUCache(int capacity) {
        this.capacity = capacity;
        this.map = new HashMap<>();
        head = new Node(0, 0);
        tail = new Node(0, 0);
        head.next = tail;
        tail.prev = head;
    }

    public int get(int key) {
        if (!map.containsKey(key)) return -1;
        Node node = map.get(key);
        moveToHead(node); // 标记为最新访问
        return node.value;
    }

    public void put(int key, int value) {
        if (map.containsKey(key)) {
            Node node = map.get(key);
            node.value = value;
            moveToHead(node);
        } else {
            Node newNode = new Node(key, value);
            map.put(key, newNode);
            addToHead(newNode);
            if (map.size() > capacity) {
                Node removed = removeTail(); // 淘汰最久未使用
                map.remove(removed.key);
            }
        }
    }

    private void addToHead(Node node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }

    private void removeNode(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    private void moveToHead(Node node) {
        removeNode(node);
        addToHead(node);
    }

    private Node removeTail() {
        Node node = tail.prev;
        removeNode(node);
        return node;
    }
}
```

## ## 手写实现链表反转

**考察重点：** 链表操作、指针移动

**解题思路：**

1. 迭代法：用三个指针 prev/curr/next 逐步翻转链表方向
2. 每次将 curr.next 指向 prev，然后三个指针同时前进一步
3. 循环结束后 prev 就是新的头节点

**关键代码：**

```java
class ListNode {
    int val;
    ListNode next;
    ListNode(int val) { this.val = val; }
}

public class ReverseLinkedList {
    // 迭代法 O(n) 时间 O(1) 空间
    public static ListNode reverse(ListNode head) {
        ListNode prev = null;
        ListNode curr = head;
        while (curr != null) {
            ListNode next = curr.next; // 暂存后继
            curr.next = prev;          // 翻转指向
            prev = curr;              // prev 前进
            curr = next;              // curr 前进
        }
        return prev; // prev 就是新的头节点
    }

    // 递归法
    public static ListNode reverseRecursive(ListNode head) {
        if (head == null || head.next == null) return head;
        ListNode newHead = reverseRecursive(head.next);
        head.next.next = head;  // 后继节点指向自己
        head.next = null;       // 断开原来的指向
        return newHead;
    }
}
```

## ## 手写实现二分查找

**考察重点：** 分治思想、边界条件处理

**解题思路：**

1. 前提：数组必须有序
2. 维护 left 和 right 两个指针表示搜索区间
3. 每次取中间位置 mid，将 target 与 arr[mid] 比较
4. 等于则找到；小于则在左半区间继续；大于则在右半区间继续
5. 注意死循环和整数溢出问题

**关键代码：**

```java
public class BinarySearch {
    // 标准二分查找
    public static int search(int[] arr, int target) {
        int left = 0, right = arr.length - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2; // 防止整数溢出
            if (arr[mid] == target) {
                return mid;
            } else if (arr[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return -1; // 未找到
    }

    // 查找第一个等于 target 的位置（处理重复元素）
    public static int searchFirst(int[] arr, int target) {
        int left = 0, right = arr.length - 1, result = -1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (arr[mid] == target) {
                result = mid;
                right = mid - 1; // 继续向左查找
            } else if (arr[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return result;
    }
}
```

## ## 手写实现快速排序

**考察重点：** 分治法、递归、原地排序

**解题思路：**

1. 选择一个基准元素 pivot（常取首元素或随机元素）
2. 分区操作（Partition）：将小于 pivot 的放左边，大于的放右边
3. 递归对左右两部分分别排序
4. 平均时间复杂度 O(n log n)，最坏 O(n²)

**关键代码：**

```java
public class QuickSort {
    public static void quickSort(int[] arr, int low, int high) {
        if (low < high) {
            int pivotIndex = partition(arr, low, high);
            quickSort(arr, low, pivotIndex - 1);  // 递归排序左半部分
            quickSort(arr, pivotIndex + 1, high);  // 递归排序右半部分
        }
    }

    private static int partition(int[] arr, int low, int high) {
        int pivot = arr[low]; // 选取首元素作为基准
        int left = low, right = high;
        while (left < right) {
            // 从右向左找到第一个小于 pivot 的元素
            while (left < right && arr[right] >= pivot) right--;
            // 从左向右找到第一个大于 pivot 的元素
            while (left < right && arr[left] <= pivot) left++;
            if (left < right) {
                int temp = arr[left];
                arr[left] = arr[right];
                arr[right] = temp;
            }
        }
        // 将 pivot 放到最终位置
        arr[low] = arr[left];
        arr[left] = pivot;
        return left;
    }

    public static void main(String[] args) {
        int[] arr = {5, 3, 8, 1, 9, 2, 7};
        quickSort(arr, 0, arr.length - 1);
        // 输出: [1, 2, 3, 5, 7, 8, 9]
    }
}
```

## ## 手写实现线程安全的阻塞队列

**考察重点：** ReentrantLock + Condition、多线程协调

**解题思路：**

1. 用数组或链表作为底层存储，维护队列头尾指针
2. 用 ReentrantLock 保证线程安全
3. 用两个 Condition 实现精准唤醒：notFull（队列不满时唤醒生产者）、notEmpty（队列不空时唤醒消费者）
4. put 时若满则 notFull.await()；take 时若空则 notEmpty.await()

**关键代码：**

```java
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public class BlockingQueue<T> {
    private final Object[] items;
    private int head, tail, count;
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition notFull = lock.newCondition();
    private final Condition notEmpty = lock.newCondition();

    public BlockingQueue(int capacity) {
        items = new Object[capacity];
    }

    public void put(T item) throws InterruptedException {
        lock.lock();
        try {
            while (count == items.length) {
                notFull.await(); // 队列满，等待消费者消费
            }
            items[tail] = item;
            tail = (tail + 1) % items.length; // 环形数组
            count++;
            notEmpty.signal(); // 唤醒消费者
        } finally {
            lock.unlock();
        }
    }

    @SuppressWarnings("unchecked")
    public T take() throws InterruptedException {
        lock.lock();
        try {
            while (count == 0) {
                notEmpty.await(); // 队列空，等待生产者生产
            }
            T item = (T) items[head];
            items[head] = null;
            head = (head + 1) % items.length;
            count--;
            notFull.signal(); // 唤醒生产者
            return item;
        } finally {
            lock.unlock();
        }
    }
}
```

## ## 手写实现字符串中第一个不重复的字符

**考察重点：** HashMap 计数、LinkedHashMap 有序性

**解题思路：**

1. 第一轮遍历：用 HashMap/数组 统计每个字符出现的次数
2. 第二轮遍历：按原始顺序找到第一个计数为 1 的字符
3. 也可以用 LinkedHashMap 一步完成（保持插入顺序）

**关键代码：**

```java
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

public class FirstUniqueChar {
    // 方法一：两次遍历
    public static char firstUnique(String s) {
        Map<Character, Integer> countMap = new HashMap<>();
        for (char c : s.toCharArray()) {
            countMap.put(c, countMap.getOrDefault(c, 0) + 1);
        }
        for (char c : s.toCharArray()) {
            if (countMap.get(c) == 1) return c;
        }
        return ' '; // 没有不重复字符
    }

    // 方法二：LinkedHashMap（保持插入顺序）
    public static char firstUniqueLHM(String s) {
        LinkedHashMap<Character, Integer> map = new LinkedHashMap<>();
        for (char c : s.toCharArray()) {
            map.put(c, map.getOrDefault(c, 0) + 1);
        }
        for (Map.Entry<Character, Integer> entry : map.entrySet()) {
            if (entry.getValue() == 1) return entry.getKey();
        }
        return ' ';
    }

    public static void main(String[] args) {
        System.out.println(firstUnique("aabcbdce")); // 输出: d
    }
}
```

## ## 手写实现两数之和

**考察重点：** HashMap 空间换时间、一次遍历

**解题思路：**

1. 暴力法：双重循环 O(n²)，不推荐
2. 哈希法：遍历数组时，用 HashMap 存储已遍历的元素（值 → 索引）
3. 每次遍历时先查 HashMap 中是否存在 target - nums[i]
4. 如果存在则找到答案；不存在则将当前元素存入 HashMap

**关键代码：**

```java
import java.util.HashMap;
import java.util.Map;

public class TwoSum {
    public static int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>(); // 值 -> 索引
        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];
            if (map.containsKey(complement)) {
                return new int[]{map.get(complement), i};
            }
            map.put(nums[i], i);
        }
        return new int[]{}; // 无解
    }

    public static void main(String[] args) {
        int[] result = twoSum(new int[]{2, 7, 11, 15}, 9);
        System.out.println(result[0] + ", " + result[1]); // 0, 1
    }
}
```

## ## 手写实现简易线程池

**考察重点：** 线程池原理、阻塞队列、线程复用

**解题思路：**

1. 线程池核心：预先创建固定数量的工作线程
2. 任务提交到阻塞队列中排队
3. 工作线程循环从队列中取任务执行（线程复用的关键）
4. 这就是 ThreadPoolExecutor 的简化版本

**关键代码：**

```java
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

public class SimpleThreadPool {
    private final BlockingQueue<Runnable> taskQueue;
    private final Thread[] workers;
    private volatile boolean isRunning = true;

    public SimpleThreadPool(int poolSize, int queueSize) {
        taskQueue = new LinkedBlockingQueue<>(queueSize);
        workers = new Thread[poolSize];
        // 预先创建并启动工作线程
        for (int i = 0; i < poolSize; i++) {
            workers[i] = new Thread(() -> {
                while (isRunning || !taskQueue.isEmpty()) {
                    try {
                        Runnable task = taskQueue.take(); // 阻塞等待任务
                        task.run();
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
            }, "Worker-" + i);
            workers[i].start();
        }
    }

    public void submit(Runnable task) {
        if (isRunning) {
            try {
                taskQueue.put(task); // 满了就阻塞等待
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    public void shutdown() {
        isRunning = false;
        for (Thread worker : workers) {
            worker.interrupt();
        }
    }

    public static void main(String[] args) {
        SimpleThreadPool pool = new SimpleThreadPool(3, 10);
        for (int i = 0; i < 10; i++) {
            int taskId = i;
            pool.submit(() -> {
                System.out.println(Thread.currentThread().getName()
                    + " 执行任务 " + taskId);
            });
        }
        pool.shutdown();
    }
}
```

## ## 手写实现 JDK 21 虚拟线程的使用

**考察重点：** JDK 21 新特性、轻量级线程、结构化并发

**解题思路：**

1. 演示两种创建方式：`Thread.ofVirtual().start()` 和线程池方式
2. 重点展示 `Executors.newVirtualThreadPerTaskExecutor()`，这是 JDK 21 处理高并发 I/O 的推荐方式
3. 对比传统线程池：虚拟线程不需要池化，随用随建，完事即销毁

**关键代码：**

```java
import java.util.concurrent.Executors;
import java.util.stream.IntStream;

public class VirtualThreadDemo {
    public static void main(String[] args) {
        // 方式一：直接创建并启动虚拟线程
        Thread vt = Thread.ofVirtual().start(() -> {
            System.out.println("运行在虚拟线程: " + Thread.currentThread());
        });

        // 方式二：使用虚拟线程执行器 (推荐用于高并发任务)
        // 这个执行器会为每个任务创建一个新的虚拟线程
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            IntStream.range(0, 10000).forEach(i -> {
                executor.submit(() -> {
                    // 模拟 I/O 阻塞
                    Thread.sleep(100);
                    return i;
                });
            });
        } // try-with-resources 会自动等待所有虚拟线程执行完毕

        System.out.println("万级任务执行完毕");
    }
}
```

## ## 手写实现 CompletableFuture 多任务编排

**考察重点：** 异步非阻塞、响应式编程思想

**解题思路：**

1. 使用 `supplyAsync` 提交异步任务
2. 使用 `thenCombine` 合并两个独立任务的结果
3. 使用 `exceptionally` 处理异常
4. 这种方式常与虚拟线程结合使用，提升系统吞吐量

**关键代码：**

```java
import java.util.concurrent.CompletableFuture;

public class AsyncComposition {
    public static void main(String[] args) {
        // 任务 1: 获取用户信息
        CompletableFuture<String> userTask = CompletableFuture.supplyAsync(() -> {
            simulateIO(500);
            return "UserA";
        });

        // 任务 2: 获取订单列表
        CompletableFuture<String> orderTask = CompletableFuture.supplyAsync(() -> {
            simulateIO(800);
            return "Order_123";
        });

        // 编排：任务 1 和 2 都完成后，进行组合处理
        CompletableFuture<String> combinedTask = userTask.thenCombine(orderTask, (user, order) -> {
            return "结果: 用户 " + user + " 的订单是 " + order;
        }).exceptionally(ex -> "出错了: " + ex.getMessage());

        System.out.println(combinedTask.join());
    }

    private static void simulateIO(int ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) {}
    }
}
```

## ## 手写实现三数之和 (Three Sum)

**考察重点：** 排序 + 双指针、去除重复解

**解题思路：**

1. 先对数组进行排序。
2. 遍历数组，固定一个数 `nums[i]`，然后用左右指针 `L = i + 1` 和 `R = n - 1` 在剩余部分寻找 `nums[L] + nums[R] == -nums[i]`。
3. 如果和大于目标值，`R--`；如果和小于目标值，`L++`。
4. **关键点**：在寻找过程中需要跳过重复的 `nums[i]`、`nums[L]` 和 `nums[R]`，以避免结果集中出现重复的三元组。

**关键代码：**

```java
import java.util.*;

public class ThreeSum {
    public List<List<Integer>> threeSum(int[] nums) {
        List<List<Integer>> ans = new ArrayList<>();
        if (nums == null || nums.length < 3) return ans;
        Arrays.sort(nums); // 排序

        for (int i = 0; i < nums.length; i++) {
            if (nums[i] > 0) break; // 如果当前数字大于0，后续和均大于0
            if (i > 0 && nums[i] == nums[i - 1]) continue; // 去重

            int L = i + 1, R = nums.length - 1;
            while (L < R) {
                int sum = nums[i] + nums[L] + nums[R];
                if (sum == 0) {
                    ans.add(Arrays.asList(nums[i], nums[L], nums[R]));
                    while (L < R && nums[L] == nums[L + 1]) L++; // 去重
                    while (L < R && nums[R] == nums[R - 1]) R--; // 去重
                    L++; R--;
                } else if (sum < 0) L++;
                else R--;
            }
        }
        return ans;
    }
}
```

## ## 手写实现冒泡排序与插入排序

**考察重点：** 基础排序原理、原地排序空间复杂度 O(1)

**解题思路：**

1. **冒泡排序**：两两比较相邻元素，每轮将最大的元素“沉底”。
2. **插入排序**：构建有序序列，对于未排序数据，在已排序序列中从后向前扫描，找到相应位置并插入（类似于整理扑克牌）。

**关键代码：**

```java
public class SortDemo {
    // 冒泡排序 O(n^2)
    public static void bubbleSort(int[] arr) {
        for (int i = 0; i < arr.length - 1; i++) {
            boolean swapped = false;
            for (int j = 0; j < arr.length - 1 - i; j++) {
                if (arr[j] > arr[j + 1]) {
                    int temp = arr[j];
                    arr[j] = arr[j + 1];
                    arr[j + 1] = temp;
                    swapped = true;
                }
            }
            if (!swapped) break; // 优化：若某轮无交换，说明已经有序
        }
    }

    // 插入排序 O(n^2)
    public static void insertionSort(int[] arr) {
        for (int i = 1; i < arr.length; i++) {
            int key = arr[i];
            int j = i - 1;
            // 将大于 key 的元素向后移
            while (j >= 0 && arr[j] > key) {
                arr[j + 1] = arr[j];
                j--;
            }
            arr[j + 1] = key;
        }
    }
}
```
