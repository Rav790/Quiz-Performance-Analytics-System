"""
seed_data.py - Generate and Insert Sample Data
================================================
Generates realistic quiz data with a fixed random seed (42) for reproducibility.

Data generated:
  - 30 students with Indian names, LPU roll numbers, realistic emails
  - 60 questions: 12 per topic (DBMS, DSA, OS, Networks, Python), mix of difficulties
  - ~300 attempts over 6 months with hidden student strength/weakness profiles

Key design decisions:
  - Fixed seed ensures everyone gets the same data for reproducible demos
  - Each student has a hidden strength profile (e.g. strong in DSA, weak in Networks)
    so aggregation analytics show meaningful patterns
  - Harder questions have lower correct probability (realistic)
  - All computed fields (correct_count, score_percent, time_taken_sec) are derived
    from the answers array, so the data is internally consistent

Usage:
    python seed_data.py
"""

import random
from datetime import datetime, timedelta
from bson import ObjectId
from config import get_database
from schema import setup_database

# Fixed seed for reproducible data
random.seed(42)

# ============================================================
# Constants
# ============================================================

BRANCHES = ["CSE", "IT", "ECE", "ME", "CIVIL"]
TOPICS = ["DBMS", "DSA", "OS", "Networks", "Python"]
DIFFICULTIES = ["easy", "medium", "hard"]

# Indian first and last names for realistic student data
FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun",
    "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Ananya", "Diya", "Myra", "Sara", "Aanya",
    "Priya", "Riya", "Neha", "Kavya", "Isha",
    "Rohan", "Karan", "Rahul", "Amit", "Vikram",
    "Sneha", "Pooja", "Divya", "Meera", "Tanvi"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Singh",
    "Kumar", "Joshi", "Rao", "Reddy", "Nair",
    "Chopra", "Malhotra", "Iyer", "Menon", "Das",
    "Bhat", "Pillai", "Chauhan", "Mishra", "Tiwari",
    "Agarwal", "Saxena", "Mehta", "Shah", "Bansal",
    "Sinha", "Kapoor", "Pandey", "Jain", "Thakur"
]

# ============================================================
# Question Bank - Real Technical Questions
# ============================================================
# Each topic has 12 questions: 4 easy, 4 medium, 4 hard

QUESTION_BANK = {
    "DBMS": [
        # Easy
        {
            "text": "What does SQL stand for?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "Structured Query Language"},
                {"key": "B", "text": "Simple Query Language"},
                {"key": "C", "text": "Standard Query Logic"},
                {"key": "D", "text": "Sequential Query Language"}
            ],
            "correct_option": "A",
            "tags": ["sql", "basics"]
        },
        {
            "text": "Which key uniquely identifies each row in a table?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "Foreign Key"},
                {"key": "B", "text": "Primary Key"},
                {"key": "C", "text": "Candidate Key"},
                {"key": "D", "text": "Super Key"}
            ],
            "correct_option": "B",
            "tags": ["keys", "basics"]
        },
        {
            "text": "Which SQL command is used to remove all rows from a table without logging individual row deletions?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "DELETE"},
                {"key": "B", "text": "DROP"},
                {"key": "C", "text": "TRUNCATE"},
                {"key": "D", "text": "REMOVE"}
            ],
            "correct_option": "C",
            "tags": ["sql", "ddl"]
        },
        {
            "text": "Which normal form eliminates partial dependency?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "1NF"},
                {"key": "B", "text": "2NF"},
                {"key": "C", "text": "3NF"},
                {"key": "D", "text": "BCNF"}
            ],
            "correct_option": "B",
            "tags": ["normalization"]
        },
        # Medium
        {
            "text": "In a relational database, what does ACID stand for in the context of transactions?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "Atomicity, Consistency, Isolation, Durability"},
                {"key": "B", "text": "Availability, Consistency, Isolation, Durability"},
                {"key": "C", "text": "Atomicity, Concurrency, Integrity, Durability"},
                {"key": "D", "text": "Atomicity, Consistency, Integrity, Distribution"}
            ],
            "correct_option": "A",
            "tags": ["transactions", "acid"]
        },
        {
            "text": "Which type of JOIN returns all rows from both tables, filling NULLs where there is no match?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "INNER JOIN"},
                {"key": "B", "text": "LEFT JOIN"},
                {"key": "C", "text": "RIGHT JOIN"},
                {"key": "D", "text": "FULL OUTER JOIN"}
            ],
            "correct_option": "D",
            "tags": ["sql", "joins"]
        },
        {
            "text": "What is the purpose of a clustered index in a database?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "It creates a separate copy of the table"},
                {"key": "B", "text": "It determines the physical order of data in the table"},
                {"key": "C", "text": "It stores only unique values"},
                {"key": "D", "text": "It automatically backs up the table"}
            ],
            "correct_option": "B",
            "tags": ["indexing", "performance"]
        },
        {
            "text": "Which isolation level allows dirty reads in SQL?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "READ COMMITTED"},
                {"key": "B", "text": "REPEATABLE READ"},
                {"key": "C", "text": "READ UNCOMMITTED"},
                {"key": "D", "text": "SERIALIZABLE"}
            ],
            "correct_option": "C",
            "tags": ["transactions", "isolation"]
        },
        # Hard
        {
            "text": "In a B+ tree index, where are the actual data pointers stored?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "In all nodes"},
                {"key": "B", "text": "Only in internal nodes"},
                {"key": "C", "text": "Only in leaf nodes"},
                {"key": "D", "text": "In the root node only"}
            ],
            "correct_option": "C",
            "tags": ["indexing", "b-tree"]
        },
        {
            "text": "Which concurrency control protocol uses timestamps to determine serializability?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "Two-Phase Locking"},
                {"key": "B", "text": "Timestamp Ordering Protocol"},
                {"key": "C", "text": "Optimistic Concurrency Control"},
                {"key": "D", "text": "Graph-based Protocol"}
            ],
            "correct_option": "B",
            "tags": ["concurrency", "transactions"]
        },
        {
            "text": "What is the difference between BCNF and 3NF?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "BCNF eliminates all transitive dependencies"},
                {"key": "B", "text": "BCNF requires every determinant to be a candidate key"},
                {"key": "C", "text": "3NF is stricter than BCNF"},
                {"key": "D", "text": "There is no difference between them"}
            ],
            "correct_option": "B",
            "tags": ["normalization"]
        },
        {
            "text": "In the CAP theorem, which two properties does MongoDB prioritize by default?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "Consistency and Availability"},
                {"key": "B", "text": "Consistency and Partition Tolerance"},
                {"key": "C", "text": "Availability and Partition Tolerance"},
                {"key": "D", "text": "All three equally"}
            ],
            "correct_option": "B",
            "tags": ["cap-theorem", "mongodb"]
        },
    ],

    "DSA": [
        # Easy
        {
            "text": "What is the time complexity of accessing an element in an array by index?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "O(1)"},
                {"key": "B", "text": "O(n)"},
                {"key": "C", "text": "O(log n)"},
                {"key": "D", "text": "O(n log n)"}
            ],
            "correct_option": "A",
            "tags": ["arrays", "complexity"]
        },
        {
            "text": "Which data structure follows the LIFO (Last In First Out) principle?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "Queue"},
                {"key": "B", "text": "Stack"},
                {"key": "C", "text": "Linked List"},
                {"key": "D", "text": "Tree"}
            ],
            "correct_option": "B",
            "tags": ["stack", "basics"]
        },
        {
            "text": "What is the maximum number of children a node can have in a binary tree?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "1"},
                {"key": "B", "text": "2"},
                {"key": "C", "text": "3"},
                {"key": "D", "text": "Unlimited"}
            ],
            "correct_option": "B",
            "tags": ["trees", "basics"]
        },
        {
            "text": "Which sorting algorithm has the best average-case time complexity?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "Bubble Sort - O(n^2)"},
                {"key": "B", "text": "Selection Sort - O(n^2)"},
                {"key": "C", "text": "Merge Sort - O(n log n)"},
                {"key": "D", "text": "Insertion Sort - O(n^2)"}
            ],
            "correct_option": "C",
            "tags": ["sorting", "complexity"]
        },
        # Medium
        {
            "text": "What is the worst-case time complexity of QuickSort?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "O(n log n)"},
                {"key": "B", "text": "O(n^2)"},
                {"key": "C", "text": "O(n)"},
                {"key": "D", "text": "O(log n)"}
            ],
            "correct_option": "B",
            "tags": ["sorting", "quicksort"]
        },
        {
            "text": "In a hash table, what technique resolves collisions by storing multiple elements in the same bucket using linked lists?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "Linear Probing"},
                {"key": "B", "text": "Quadratic Probing"},
                {"key": "C", "text": "Separate Chaining"},
                {"key": "D", "text": "Double Hashing"}
            ],
            "correct_option": "C",
            "tags": ["hashing", "collision"]
        },
        {
            "text": "Which traversal of a Binary Search Tree gives elements in sorted order?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "Preorder"},
                {"key": "B", "text": "Inorder"},
                {"key": "C", "text": "Postorder"},
                {"key": "D", "text": "Level Order"}
            ],
            "correct_option": "B",
            "tags": ["bst", "traversal"]
        },
        {
            "text": "What is the space complexity of BFS graph traversal?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "O(V)"},
                {"key": "B", "text": "O(E)"},
                {"key": "C", "text": "O(V + E)"},
                {"key": "D", "text": "O(V * E)"}
            ],
            "correct_option": "A",
            "tags": ["graphs", "bfs"]
        },
        # Hard
        {
            "text": "What is the amortized time complexity of inserting an element into a dynamic array (like Python's list)?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "O(n)"},
                {"key": "B", "text": "O(1)"},
                {"key": "C", "text": "O(log n)"},
                {"key": "D", "text": "O(n log n)"}
            ],
            "correct_option": "B",
            "tags": ["dynamic-array", "amortized"]
        },
        {
            "text": "Which algorithm finds the shortest path in a weighted graph with negative edge weights (but no negative cycles)?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "Dijkstra's Algorithm"},
                {"key": "B", "text": "Bellman-Ford Algorithm"},
                {"key": "C", "text": "Floyd-Warshall Algorithm"},
                {"key": "D", "text": "Kruskal's Algorithm"}
            ],
            "correct_option": "B",
            "tags": ["graphs", "shortest-path"]
        },
        {
            "text": "What is the time complexity of building a heap from an unsorted array?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "O(n log n)"},
                {"key": "B", "text": "O(n^2)"},
                {"key": "C", "text": "O(n)"},
                {"key": "D", "text": "O(log n)"}
            ],
            "correct_option": "C",
            "tags": ["heap", "complexity"]
        },
        {
            "text": "In the context of dynamic programming, what does 'optimal substructure' mean?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "The problem can be divided into independent subproblems"},
                {"key": "B", "text": "An optimal solution contains optimal solutions to its subproblems"},
                {"key": "C", "text": "The problem has overlapping subproblems"},
                {"key": "D", "text": "The problem can be solved greedily"}
            ],
            "correct_option": "B",
            "tags": ["dp", "theory"]
        },
    ],

    "OS": [
        # Easy
        {
            "text": "What is the main function of an operating system?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "Compile programs"},
                {"key": "B", "text": "Manage hardware and software resources"},
                {"key": "C", "text": "Design user interfaces"},
                {"key": "D", "text": "Connect to the internet"}
            ],
            "correct_option": "B",
            "tags": ["basics"]
        },
        {
            "text": "Which of the following is NOT a type of operating system?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "Batch OS"},
                {"key": "B", "text": "Real-time OS"},
                {"key": "C", "text": "Compiler OS"},
                {"key": "D", "text": "Distributed OS"}
            ],
            "correct_option": "C",
            "tags": ["types", "basics"]
        },
        {
            "text": "What is a process in operating system terminology?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "A file stored on disk"},
                {"key": "B", "text": "A program in execution"},
                {"key": "C", "text": "A hardware component"},
                {"key": "D", "text": "A user interface element"}
            ],
            "correct_option": "B",
            "tags": ["process", "basics"]
        },
        {
            "text": "Which scheduling algorithm gives the minimum average waiting time?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "FCFS"},
                {"key": "B", "text": "SJF (Non-preemptive)"},
                {"key": "C", "text": "Round Robin"},
                {"key": "D", "text": "Priority Scheduling"}
            ],
            "correct_option": "B",
            "tags": ["scheduling"]
        },
        # Medium
        {
            "text": "What are the four necessary conditions for a deadlock to occur?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "Mutual exclusion, Hold & wait, No preemption, Circular wait"},
                {"key": "B", "text": "Starvation, Blocking, Locking, Waiting"},
                {"key": "C", "text": "Mutual exclusion, Priority inversion, Blocking, Circular wait"},
                {"key": "D", "text": "Hold & wait, Preemption, Starvation, Locking"}
            ],
            "correct_option": "A",
            "tags": ["deadlock"]
        },
        {
            "text": "In virtual memory, what is a page fault?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "An error in the page table"},
                {"key": "B", "text": "When a referenced page is not in physical memory"},
                {"key": "C", "text": "When two processes access the same page"},
                {"key": "D", "text": "When the page size is too large"}
            ],
            "correct_option": "B",
            "tags": ["memory", "virtual-memory"]
        },
        {
            "text": "Which page replacement algorithm suffers from Belady's anomaly?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "LRU"},
                {"key": "B", "text": "Optimal"},
                {"key": "C", "text": "FIFO"},
                {"key": "D", "text": "LFU"}
            ],
            "correct_option": "C",
            "tags": ["memory", "page-replacement"]
        },
        {
            "text": "What is the purpose of a semaphore in process synchronization?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "To increase process speed"},
                {"key": "B", "text": "To control access to shared resources"},
                {"key": "C", "text": "To allocate memory to processes"},
                {"key": "D", "text": "To schedule CPU time"}
            ],
            "correct_option": "B",
            "tags": ["synchronization", "semaphore"]
        },
        # Hard
        {
            "text": "In the Banker's algorithm, what does the 'Need' matrix represent?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "Currently allocated resources"},
                {"key": "B", "text": "Maximum resources minus allocated resources"},
                {"key": "C", "text": "Total available resources"},
                {"key": "D", "text": "Resources requested by each process"}
            ],
            "correct_option": "B",
            "tags": ["deadlock", "bankers"]
        },
        {
            "text": "What is thrashing in an operating system?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "When CPU utilization is at 100%"},
                {"key": "B", "text": "When the system spends more time paging than executing"},
                {"key": "C", "text": "When too many processes are in the ready queue"},
                {"key": "D", "text": "When disk I/O is very slow"}
            ],
            "correct_option": "B",
            "tags": ["memory", "thrashing"]
        },
        {
            "text": "Which disk scheduling algorithm can cause starvation of requests at the extremes?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "FCFS"},
                {"key": "B", "text": "SSTF"},
                {"key": "C", "text": "SCAN"},
                {"key": "D", "text": "C-LOOK"}
            ],
            "correct_option": "B",
            "tags": ["disk", "scheduling"]
        },
        {
            "text": "What is the difference between a process and a thread in terms of memory sharing?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "Processes share memory; threads do not"},
                {"key": "B", "text": "Threads share the process's memory space; processes have separate address spaces"},
                {"key": "C", "text": "Both share the same memory space"},
                {"key": "D", "text": "Neither shares memory"}
            ],
            "correct_option": "B",
            "tags": ["process", "thread"]
        },
    ],

    "Networks": [
        # Easy
        {
            "text": "Which layer of the OSI model is responsible for routing?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "Data Link Layer"},
                {"key": "B", "text": "Network Layer"},
                {"key": "C", "text": "Transport Layer"},
                {"key": "D", "text": "Session Layer"}
            ],
            "correct_option": "B",
            "tags": ["osi", "routing"]
        },
        {
            "text": "What does HTTP stand for?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "HyperText Transfer Protocol"},
                {"key": "B", "text": "High Transfer Text Protocol"},
                {"key": "C", "text": "HyperText Transmission Process"},
                {"key": "D", "text": "Hyper Transfer Text Protocol"}
            ],
            "correct_option": "A",
            "tags": ["protocols", "http"]
        },
        {
            "text": "Which device operates at Layer 2 of the OSI model?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "Router"},
                {"key": "B", "text": "Switch"},
                {"key": "C", "text": "Hub"},
                {"key": "D", "text": "Modem"}
            ],
            "correct_option": "B",
            "tags": ["devices", "osi"]
        },
        {
            "text": "What is the default port number for HTTPS?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "80"},
                {"key": "B", "text": "443"},
                {"key": "C", "text": "8080"},
                {"key": "D", "text": "21"}
            ],
            "correct_option": "B",
            "tags": ["ports", "https"]
        },
        # Medium
        {
            "text": "What is the purpose of the ARP protocol?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "Resolve domain names to IP addresses"},
                {"key": "B", "text": "Resolve IP addresses to MAC addresses"},
                {"key": "C", "text": "Route packets across networks"},
                {"key": "D", "text": "Encrypt network traffic"}
            ],
            "correct_option": "B",
            "tags": ["arp", "protocols"]
        },
        {
            "text": "In TCP, what is the purpose of the three-way handshake?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "To encrypt the connection"},
                {"key": "B", "text": "To establish a reliable connection between client and server"},
                {"key": "C", "text": "To authenticate the user"},
                {"key": "D", "text": "To resolve the IP address"}
            ],
            "correct_option": "B",
            "tags": ["tcp", "handshake"]
        },
        {
            "text": "What is the difference between TCP and UDP?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "TCP is faster; UDP is more reliable"},
                {"key": "B", "text": "TCP is connection-oriented and reliable; UDP is connectionless and faster"},
                {"key": "C", "text": "Both are connection-oriented"},
                {"key": "D", "text": "UDP guarantees delivery; TCP does not"}
            ],
            "correct_option": "B",
            "tags": ["tcp", "udp"]
        },
        {
            "text": "What does a subnet mask determine?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "The speed of the network"},
                {"key": "B", "text": "Which part of an IP address is the network and which is the host"},
                {"key": "C", "text": "The encryption level"},
                {"key": "D", "text": "The default gateway"}
            ],
            "correct_option": "B",
            "tags": ["subnetting", "ip"]
        },
        # Hard
        {
            "text": "In BGP (Border Gateway Protocol), what type of routing algorithm is used?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "Distance Vector"},
                {"key": "B", "text": "Link State"},
                {"key": "C", "text": "Path Vector"},
                {"key": "D", "text": "Flooding"}
            ],
            "correct_option": "C",
            "tags": ["bgp", "routing"]
        },
        {
            "text": "What is the maximum window size in TCP without window scaling?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "1024 bytes"},
                {"key": "B", "text": "16384 bytes"},
                {"key": "C", "text": "65535 bytes"},
                {"key": "D", "text": "1048576 bytes"}
            ],
            "correct_option": "C",
            "tags": ["tcp", "window"]
        },
        {
            "text": "Which protocol is used for secure email transmission?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "SMTP over TLS (SMTPS)"},
                {"key": "B", "text": "FTP"},
                {"key": "C", "text": "SNMP"},
                {"key": "D", "text": "ICMP"}
            ],
            "correct_option": "A",
            "tags": ["email", "security"]
        },
        {
            "text": "In CIDR notation, what does /24 signify?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "24 hosts in the network"},
                {"key": "B", "text": "24 bits for the network portion, 8 bits for hosts"},
                {"key": "C", "text": "24 subnets available"},
                {"key": "D", "text": "24 routers in the path"}
            ],
            "correct_option": "B",
            "tags": ["cidr", "subnetting"]
        },
    ],

    "Python": [
        # Easy
        {
            "text": "Which keyword is used to define a function in Python?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "function"},
                {"key": "B", "text": "def"},
                {"key": "C", "text": "func"},
                {"key": "D", "text": "define"}
            ],
            "correct_option": "B",
            "tags": ["functions", "basics"]
        },
        {
            "text": "What is the output of: print(type([]))?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "<class 'tuple'>"},
                {"key": "B", "text": "<class 'dict'>"},
                {"key": "C", "text": "<class 'list'>"},
                {"key": "D", "text": "<class 'set'>"}
            ],
            "correct_option": "C",
            "tags": ["types", "basics"]
        },
        {
            "text": "Which of the following is an immutable data type in Python?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "List"},
                {"key": "B", "text": "Dictionary"},
                {"key": "C", "text": "Set"},
                {"key": "D", "text": "Tuple"}
            ],
            "correct_option": "D",
            "tags": ["types", "immutable"]
        },
        {
            "text": "How do you start a comment in Python?",
            "difficulty": "easy",
            "options": [
                {"key": "A", "text": "//"},
                {"key": "B", "text": "#"},
                {"key": "C", "text": "/*"},
                {"key": "D", "text": "--"}
            ],
            "correct_option": "B",
            "tags": ["syntax", "basics"]
        },
        # Medium
        {
            "text": "What is the difference between a list and a tuple in Python?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "Lists are immutable; tuples are mutable"},
                {"key": "B", "text": "Lists are mutable; tuples are immutable"},
                {"key": "C", "text": "Both are mutable"},
                {"key": "D", "text": "Both are immutable"}
            ],
            "correct_option": "B",
            "tags": ["types", "mutability"]
        },
        {
            "text": "What does the 'self' parameter refer to in a Python class method?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "The class itself"},
                {"key": "B", "text": "The current instance of the class"},
                {"key": "C", "text": "The parent class"},
                {"key": "D", "text": "A global variable"}
            ],
            "correct_option": "B",
            "tags": ["oop", "classes"]
        },
        {
            "text": "What will list(range(5)) return?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "[1, 2, 3, 4, 5]"},
                {"key": "B", "text": "[0, 1, 2, 3, 4]"},
                {"key": "C", "text": "[0, 1, 2, 3, 4, 5]"},
                {"key": "D", "text": "[1, 2, 3, 4]"}
            ],
            "correct_option": "B",
            "tags": ["range", "basics"]
        },
        {
            "text": "Which built-in function returns the number of items in a container?",
            "difficulty": "medium",
            "options": [
                {"key": "A", "text": "count()"},
                {"key": "B", "text": "size()"},
                {"key": "C", "text": "len()"},
                {"key": "D", "text": "length()"}
            ],
            "correct_option": "C",
            "tags": ["built-ins"]
        },
        # Hard
        {
            "text": "What is a Python decorator?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "A function that takes a function and extends its behavior"},
                {"key": "B", "text": "A special type of class"},
                {"key": "C", "text": "A way to define constants"},
                {"key": "D", "text": "A loop optimization technique"}
            ],
            "correct_option": "A",
            "tags": ["decorators", "advanced"]
        },
        {
            "text": "What is the Global Interpreter Lock (GIL) in CPython?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "A lock that prevents multiple Python processes"},
                {"key": "B", "text": "A mutex that allows only one thread to execute Python bytecode at a time"},
                {"key": "C", "text": "A security feature that prevents unauthorized access"},
                {"key": "D", "text": "A garbage collection mechanism"}
            ],
            "correct_option": "B",
            "tags": ["threading", "gil"]
        },
        {
            "text": "What is the difference between __str__ and __repr__ in Python?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "__str__ is for developers; __repr__ is for end users"},
                {"key": "B", "text": "__str__ returns a readable string; __repr__ returns an unambiguous string for debugging"},
                {"key": "C", "text": "They are exactly the same"},
                {"key": "D", "text": "__repr__ is called by print(); __str__ is not"}
            ],
            "correct_option": "B",
            "tags": ["magic-methods", "oop"]
        },
        {
            "text": "How does Python's garbage collector handle circular references?",
            "difficulty": "hard",
            "options": [
                {"key": "A", "text": "It cannot handle them; they cause memory leaks"},
                {"key": "B", "text": "It uses a generational garbage collector that detects and collects circular references"},
                {"key": "C", "text": "It uses manual memory management"},
                {"key": "D", "text": "It uses reference counting only"}
            ],
            "correct_option": "B",
            "tags": ["gc", "memory"]
        },
    ],
}


# ============================================================
# Data Generators
# ============================================================

def generate_students(count=30):
    """
    Generate student documents with Indian names, LPU roll numbers,
    college-style emails, and spread across branches/semesters.
    """
    students = []
    now = datetime.now()

    for i in range(count):
        first = FIRST_NAMES[i]
        last = LAST_NAMES[i]
        name = f"{first} {last}"
        roll_no = f"LPU2026{str(i + 1).zfill(3)}"
        email = f"{first.lower()}.{roll_no.lower()}@lpu.in"
        branch = BRANCHES[i % len(BRANCHES)]
        semester = random.choice([5, 6, 7, 8])
        # Created sometime in the past 2 years
        created_at = now - timedelta(days=random.randint(30, 730))

        students.append({
            "roll_no": roll_no,
            "name": name,
            "email": email,
            "branch": branch,
            "semester": semester,
            "is_active": True,
            "created_at": created_at
        })

    return students


def generate_questions():
    """
    Build question documents from the hand-written question bank.
    Adds topic, marks (1 for easy, 2 for medium, 3 for hard), and a timestamp.
    """
    questions = []
    now = datetime.now()

    for topic, topic_questions in QUESTION_BANK.items():
        for q in topic_questions:
            # Marks scale with difficulty to reward harder questions
            marks_map = {"easy": 1, "medium": 2, "hard": 3}
            questions.append({
                "topic": topic,
                "difficulty": q["difficulty"],
                "text": q["text"],
                "options": q["options"],
                "correct_option": q["correct_option"],
                "marks": marks_map[q["difficulty"]],
                "tags": q.get("tags", []),
                "created_at": now - timedelta(days=random.randint(1, 180))
            })

    return questions


def generate_attempts(student_ids, question_docs, count=300):
    """
    Generate quiz attempt documents with hidden student strength profiles.

    Each student gets a random strength profile:
      - Two strong topics (higher probability of correct answers)
      - Remaining topics are weaker

    Harder questions have lower base probability of being correct.
    This ensures aggregation analytics show meaningful patterns (weak topics, etc.).
    """
    attempts = []
    now = datetime.now()

    # Build question lookup by ID for quick access
    questions_by_id = {q["_id"]: q for q in question_docs}
    questions_by_topic = {}
    for q in question_docs:
        questions_by_topic.setdefault(q["topic"], []).append(q)

    # Quiz title templates
    quiz_templates = [
        "{topic} Weekly Quiz {n}",
        "{topic} Practice Test {n}",
        "{topic} Mid-Term Mock {n}",
        "{topic} Assessment {n}",
    ]

    # Create a hidden strength profile for each student
    # Each student is "strong" in 2 random topics and "weak" in the rest
    student_profiles = {}
    for sid in student_ids:
        strong_topics = set(random.sample(TOPICS, 2))
        student_profiles[sid] = strong_topics

    for _ in range(count):
        student_id = random.choice(student_ids)
        strong_topics = student_profiles[student_id]

        # Pick a primary topic for this quiz (weighted toward all topics)
        primary_topic = random.choice(TOPICS)
        quiz_n = random.randint(1, 5)
        template = random.choice(quiz_templates)
        quiz_title = template.format(topic=primary_topic, n=quiz_n)

        # Pick 10 questions: 6-7 from the primary topic, rest from others
        primary_count = random.randint(6, 7)
        other_count = 10 - primary_count

        primary_qs = random.choices(questions_by_topic[primary_topic], k=primary_count)
        other_topics = [t for t in TOPICS if t != primary_topic]
        other_qs = []
        for _ in range(other_count):
            t = random.choice(other_topics)
            other_qs.append(random.choice(questions_by_topic[t]))

        selected_questions = primary_qs + other_qs
        random.shuffle(selected_questions)

        # Generate answers with strength-based probabilities
        answers = []
        for q in selected_questions:
            topic = q["topic"]
            difficulty = q["difficulty"]

            # Base probability of getting it right
            diff_probs = {"easy": 0.75, "medium": 0.55, "hard": 0.35}
            prob = diff_probs[difficulty]

            # Boost for strong topics, penalty for weak ones
            if topic in strong_topics:
                prob = min(prob + 0.15, 0.95)
            else:
                prob = max(prob - 0.10, 0.15)

            is_correct = random.random() < prob

            if is_correct:
                selected_option = q["correct_option"]
            else:
                # Pick a wrong answer
                wrong_options = [o for o in ["A", "B", "C", "D"] if o != q["correct_option"]]
                # Small chance of not answering (null)
                if random.random() < 0.05:
                    selected_option = None
                else:
                    selected_option = random.choice(wrong_options)

            # Time spent: harder questions take more time
            time_ranges = {"easy": (10, 35), "medium": (20, 55), "hard": (30, 90)}
            low, high = time_ranges[difficulty]
            time_spent = random.randint(low, high)

            answers.append({
                "question_id": q["_id"],
                "topic": topic,
                "difficulty": difficulty,
                "selected_option": selected_option,
                "is_correct": is_correct,
                "time_spent_sec": time_spent
            })

        # Compute derived fields from the answers (data consistency!)
        correct_count = sum(1 for a in answers if a["is_correct"])
        total_questions = len(answers)
        score_percent = round((correct_count / total_questions) * 100, 2)
        time_taken_sec = sum(a["time_spent_sec"] for a in answers)

        # Attempted sometime in the last 6 months
        attempted_at = now - timedelta(
            days=random.randint(0, 180),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        attempts.append({
            "student_id": student_id,
            "quiz_title": quiz_title,
            "attempted_at": attempted_at,
            "time_taken_sec": time_taken_sec,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "score_percent": float(score_percent),  # Ensure it's a double for MongoDB
            "answers": answers
        })

    return attempts


# ============================================================
# Main Seed Function
# ============================================================

def seed_database(db):
    """
    Generate all data and insert into the database.
    Prints a summary of counts per collection.
    """
    print("\n=== Seeding Database ===\n")

    # --- Students ---
    print("Generating students...")
    students = generate_students(30)
    result = db.students.insert_many(students, ordered=False)
    student_ids = result.inserted_ids
    print(f"  Inserted {len(student_ids)} students")

    # --- Questions ---
    print("Generating questions...")
    questions = generate_questions()
    result = db.questions.insert_many(questions, ordered=False)
    question_ids = result.inserted_ids
    print(f"  Inserted {len(question_ids)} questions")

    # Fetch the full question docs (we need _id for attempts)
    question_docs = list(db.questions.find())

    # --- Attempts ---
    print("Generating attempts...")
    attempts = generate_attempts(student_ids, question_docs, count=300)
    # Insert in batches of 100 for efficiency
    batch_size = 100
    total_inserted = 0
    for i in range(0, len(attempts), batch_size):
        batch = attempts[i:i + batch_size]
        result = db.attempts.insert_many(batch, ordered=False)
        total_inserted += len(result.inserted_ids)
    print(f"  Inserted {total_inserted} attempts")

    # --- Summary ---
    print("\n=== Seed Summary ===")
    print(f"  students:  {db.students.count_documents({})}")
    print(f"  questions: {db.questions.count_documents({})}")
    print(f"  attempts:  {db.attempts.count_documents({})}")
    print()


if __name__ == "__main__":
    db = get_database()

    # Reset and recreate schema before seeding
    setup_database(db, reset=True)

    # Seed with fresh data
    seed_database(db)
    print("[DONE] Database seeded successfully!")
