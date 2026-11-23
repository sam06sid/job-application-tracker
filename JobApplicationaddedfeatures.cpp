#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <queue>
#include <stack>
#include <algorithm>
#include <cstdlib>
#include <cctype>

using namespace std;

class Application {
public:
    int id;
    string company, role, field, deadline, status;
    int urgency;
};

template <class T, class Compare>
void mergeSort(vector<T>& a, int l, int r, Compare comp) {
    if (l >= r) return;
    int mid = (l + r) / 2;

    mergeSort(a, l, mid, comp);
    mergeSort(a, mid + 1, r, comp);

    vector<T> temp;
    int i = l, j = mid + 1;

    while (i <= mid && j <= r) {
        if (comp(a[i], a[j]))
            temp.push_back(a[i++]);
        else
            temp.push_back(a[j++]);
    }

    while (i <= mid) temp.push_back(a[i++]);
    while (j <= r) temp.push_back(a[j++]);

    for (int k = 0; k < (int)temp.size(); k++)
        a[l + k] = temp[k];
}

class StringLess {
public:
    bool operator()(const string& a, const string& b) const {
        return a < b;
    }
};

class DeadlineLess {
public:
    bool operator()(const Application& a, const Application& b) const {
        return a.deadline < b.deadline;
    }
};

class Node {
public:
    Application app;
    Node* next;

    Node(Application a) {
        app = a;
        next = NULL;
    }
};

class HashTable {
    static const int SIZE = 101;
    vector<pair<string, vector<int> > > table[SIZE];

    int hashFunction(string key) {
        int hash = 0;

        for (int i = 0; i < (int)key.length(); i++)
            hash = (hash * 31 + key[i]) % SIZE;

        return hash;
    }

public:
    void insert(string company, int id) {
        int index = hashFunction(company);

        for (int i = 0; i < (int)table[index].size(); i++) {
            if (table[index][i].first == company) {
                table[index][i].second.push_back(id);
                return;
            }
        }

        vector<int> ids;
        ids.push_back(id);
        table[index].push_back(make_pair(company, ids));
    }

    vector<int>* search(string company) {
        int index = hashFunction(company);

        for (int i = 0; i < (int)table[index].size(); i++) {
            if (table[index][i].first == company)
                return &table[index][i].second;
        }

        return NULL;
    }

    void clear() {
        for (int i = 0; i < SIZE; i++)
            table[i].clear();
    }
};

class TreeNode {
public:
    string deadline;
    vector<int> ids;
    TreeNode *left, *right;

    TreeNode(string d, int id) {
        deadline = d;
        ids.push_back(id);
        left = right = NULL;
    }
};

class DeadlineBST {
    TreeNode* root;

    TreeNode* insert(TreeNode* node, string date, int id) {
        if (node == NULL)
            return new TreeNode(date, id);

        if (date < node->deadline)
            node->left = insert(node->left, date, id);
        else if (date > node->deadline)
            node->right = insert(node->right, date, id);
        else
            node->ids.push_back(id);

        return node;
    }

    void inorder(TreeNode* node) {
        if (node == NULL) return;

        inorder(node->left);

        cout << "Deadline: " << node->deadline << " | IDs: ";

        for (int i = 0; i < (int)node->ids.size(); i++)
            cout << node->ids[i] << " ";

        cout << endl;

        inorder(node->right);
    }

    void destroy(TreeNode* node) {
        if (node == NULL) return;

        destroy(node->left);
        destroy(node->right);
        delete node;
    }

public:
    DeadlineBST() {
        root = NULL;
    }

    ~DeadlineBST() {
        destroy(root);
    }

    void clear() {
        destroy(root);
        root = NULL;
    }

    void insert(string date, int id) {
        root = insert(root, date, id);
    }

    void display() {
        if (root == NULL) {
            cout << "No deadlines available.\n";
            return;
        }

        cout << "\nAPPLICATIONS BY DEADLINE\n";
        inorder(root);
    }
};

class HeapItem {
public:
    int id, urgency;
    string deadline;
};

class MinHeap {
    vector<HeapItem> heap;

    bool smaller(HeapItem a, HeapItem b) {
        if (a.urgency != b.urgency)
            return a.urgency < b.urgency;

        return a.deadline < b.deadline;
    }

    void heapifyUp(int i) {
        while (i > 0) {
            int p = (i - 1) / 2;

            if (smaller(heap[i], heap[p])) {
                swap(heap[i], heap[p]);
                i = p;
            }
            else {
                break;
            }
        }
    }

    void heapifyDown(int i) {
        int n = (int)heap.size();

        while (true) {
            int s = i;
            int l = 2 * i + 1;
            int r = 2 * i + 2;

            if (l < n && smaller(heap[l], heap[s]))
                s = l;

            if (r < n && smaller(heap[r], heap[s]))
                s = r;

            if (s == i) break;

            swap(heap[i], heap[s]);
            i = s;
        }
    }

public:
    void insert(HeapItem item) {
        heap.push_back(item);
        heapifyUp((int)heap.size() - 1);
    }

    bool empty() {
        return heap.empty();
    }

    HeapItem pop() {
        HeapItem result = heap[0];

        heap[0] = heap.back();
        heap.pop_back();

        if (!heap.empty())
            heapifyDown(0);

        return result;
    }

    void display() {
        if (heap.empty()) {
            cout << "No applications available.\n";
            return;
        }

        MinHeap temp = *this;

        cout << "\nURGENCY RANKING\n";

        while (!temp.empty()) {
            HeapItem x = temp.pop();

            cout << "ID: " << x.id
                 << " | Urgency: " << x.urgency
                 << " | Deadline: " << x.deadline << endl;
        }
    }

    void clear() {
        heap.clear();
    }
};

class UndoAction {
public:
    string type, oldStatus;
    int id;
};

class JobTracker {
    Node* head;
    int nextID;

    HashTable hashTable;
    DeadlineBST bst;
    MinHeap heap;

    stack<UndoAction> undoStack;
    queue<int> interviewQueue;

    map<string, vector<string> > graph;
    string normalizeText(string value) {
        string result = "";

        for (int i = 0; i < (int)value.length(); i++) {
            if (!isspace((unsigned char)value[i]) && value[i] != '-') {
                result += (char)tolower((unsigned char)value[i]);
            }
        }

        return result;
    }

    string getFieldCategory(string field) {
        string value = normalizeText(field);

        if (value == "softwareengineering" ||
            value == "softwaredevelopment" ||
            value == "programming") {
            return "software";
        }

        if (value == "ai" ||
            value == "artificialintelligence" ||
            value == "machinelearning") {
            return "ai";
        }

        if (value == "cybersecurity" ||
            value == "informationsecurity") {
            return "cybersecurity";
        }

        if (value == "networking" || value == "network") {
            return "networking";
        }

        if (value == "datascience" || value == "dataanalytics") {
            return "datascience";
        }

        if (value == "webdevelopment" || value == "webdesign") {
            return "web";
        }

        if (value == "database" ||
            value == "databaseadministration" ||
            value == "databasemanagement") {
            return "database";
        }

        return value;
    }

    Node* findID(int id) {
        Node* p = head;

        while (p != NULL) {
            if (p->app.id == id)
                return p;

            p = p->next;
        }

        return NULL;
    }

    void removeID(int id) {
        Node *p = head, *prev = NULL;

        while (p != NULL) {
            if (p->app.id == id) {
                if (prev == NULL)
                    head = p->next;
                else
                    prev->next = p->next;

                delete p;
                return;
            }

            prev = p;
            p = p->next;
        }
    }

    void rebuild() {
        hashTable.clear();
        bst.clear();
        heap.clear();

        Node* p = head;

        while (p != NULL) {
            Application a = p->app;

            hashTable.insert(a.company, a.id);
            bst.insert(a.deadline, a.id);

            HeapItem h;
            h.id = a.id;
            h.urgency = a.urgency;
            h.deadline = a.deadline;

            heap.insert(h);

            p = p->next;
        }
    }

    int countApps(Node* p) {
        if (p == NULL) return 0;

        return 1 + countApps(p->next);
    }

    int countStatus(Node* p, string status) {
        if (p == NULL) return 0;

        return (p->app.status == status)
             + countStatus(p->next, status);
    }

public:

    JobTracker() {
        head = NULL;
        nextID = 1;
    }

    ~JobTracker() {
        while (head != NULL) {
            Node* temp = head;
            head = head->next;
            delete temp;
        }
    }

    void addApplication() {
        Application a;
        a.id = nextID;

        cout << "\nCompany: ";
        getline(cin, a.company);

        cout << "Job Role: ";
        getline(cin, a.role);

        cout << "Job Field: ";
        getline(cin, a.field);

        cout << "Deadline (YYYY-MM-DD): ";
        getline(cin, a.deadline);

        cout << "Status: ";
        getline(cin, a.status);

        cout << "Urgency (1-5): ";
        cin >> a.urgency;
        cin.ignore(10000, '\n');

        if (a.company.empty() || a.role.empty() || a.field.empty() ||
            a.deadline.length() != 10 ||
            a.deadline[4] != '-' || a.deadline[7] != '-' ||
            a.urgency < 1 || a.urgency > 5) {

            cout << "Invalid input. Application not added.\n";
            return;
        }

        Node* newNode = new Node(a);

        if (head == NULL) {
            head = newNode;
        }
        else {
            Node* p = head;

            while (p->next != NULL)
                p = p->next;

            p->next = newNode;
        }

        UndoAction action;
        action.type = "ADD";
        action.id = a.id;

        undoStack.push(action);

        nextID++;
        rebuild();

        cout << "Application added! ID: " << a.id << endl;
    }

    void display() {
        if (head == NULL) {
            cout << "No applications found.\n";
            return;
        }

        Node* p = head;

        cout << "\nALL JOB APPLICATIONS\n";

        while (p != NULL) {
            Application a = p->app;

            cout << "\nID: " << a.id
                 << "\nCompany: " << a.company
                 << "\nRole: " << a.role
                 << "\nField: " << a.field
                 << "\nDeadline: " << a.deadline
                 << "\nStatus: " << a.status
                 << "\nUrgency: " << a.urgency
                 << "\n-------------------------\n";

            p = p->next;
        }
    }

    void searchCompany() {
        string name;

        cout << "Enter company name: ";
        getline(cin, name);

        vector<int>* ids = hashTable.search(name);

        if (ids == NULL) {
            cout << "Company not found.\n";
            return;
        }

        for (int i = 0; i < (int)ids->size(); i++) {
            Node* p = findID((*ids)[i]);

            if (p != NULL) {
                cout << "\nID: " << p->app.id
                     << "\nCompany: " << p->app.company
                     << "\nRole: " << p->app.role
                     << "\nStatus: " << p->app.status << endl;
            }
        }
    }

    void binarySearchCompany() {
        vector<string> names;

        Node* p = head;

        while (p != NULL) {
            names.push_back(p->app.company);
            p = p->next;
        }

        if (names.empty()) {
            cout << "No companies available.\n";
            return;
        }

        mergeSort<string>(
            names, 0, (int)names.size() - 1, StringLess()
        );

        names.erase(
            unique(names.begin(), names.end()), names.end()
        );

        string target;

        cout << "Enter company name: ";
        getline(cin, target);

        int l = 0;
        int r = (int)names.size() - 1;
        bool found = false;

        while (l <= r) {
            int mid = l + (r - l) / 2;

            if (names[mid] == target) {
                found = true;
                break;
            }

            if (names[mid] < target)
                l = mid + 1;
            else
                r = mid - 1;
        }

        if (found)
            cout << "Company found using Binary Search!\n";
        else
            cout << "Company not found.\n";
    }

    void showDeadlines() {
        bst.display();
    }

    void showUrgency() {
        heap.display();
    }

    void updateStatus() {
        int id;

        cout << "Enter Application ID: ";
        cin >> id;
        cin.ignore(10000, '\n');

        Node* p = findID(id);

        if (p == NULL) {
            cout << "Application not found.\n";
            return;
        }

        UndoAction action;
        action.type = "STATUS";
        action.id = id;
        action.oldStatus = p->app.status;

        undoStack.push(action);

        cout << "Enter new status: ";
        getline(cin, p->app.status);

        if (p->app.status == "Interview")
            interviewQueue.push(id);

        rebuild();

        cout << "Status updated successfully!\n";
    }

    void undo() {
        if (undoStack.empty()) {
            cout << "Nothing to undo.\n";
            return;
        }

        UndoAction a = undoStack.top();
        undoStack.pop();

        if (a.type == "ADD") {
            removeID(a.id);

            cout << "Application addition undone.\n";
        }
        else {
            Node* p = findID(a.id);

            if (p != NULL) {
                p->app.status = a.oldStatus;

                cout << "Previous status restored.\n";
            }
        }

        rebuild();
    }

    void showQueue() {
        if (interviewQueue.empty()) {
            cout << "Interview queue is empty.\n";
            return;
        }

        queue<int> temp = interviewQueue;

        cout << "\nINTERVIEW PREPARATION QUEUE\n";

        while (!temp.empty()) {
            int id = temp.front();
            temp.pop();

            Node* p = findID(id);

            if (p != NULL && p->app.status == "Interview")
                cout << p->app.company << " - "
                     << p->app.role << endl;
        }
    }

    void processInterview() {
        while (!interviewQueue.empty()) {
            int id = interviewQueue.front();
            interviewQueue.pop();

            Node* p = findID(id);

            if (p != NULL && p->app.status == "Interview") {
                cout << "Preparing for: " << p->app.company
                     << " - " << p->app.role << endl;

                return;
            }
        }

        cout << "No pending interviews.\n";
    }

    void addConnection() {
        string a, b;

        cout << "First company: ";
        getline(cin, a);

        cout << "Related company: ";
        getline(cin, b);

        if (a.empty() || b.empty() || a == b) {
            cout << "Invalid connection.\n";
            return;
        }

        graph[a];
        graph[b];

        if (find(graph[a].begin(), graph[a].end(), b)
            == graph[a].end())
            graph[a].push_back(b);

        if (find(graph[b].begin(), graph[b].end(), a)
            == graph[b].end())
            graph[b].push_back(a);

        cout << "Connection added!\n";
    }

    void BFS() {
        string start;

        cout << "Starting company: ";
        getline(cin, start);

        if (graph.find(start) == graph.end()) {
            cout << "Company not found in graph.\n";
            return;
        }

        queue<string> q;
        vector<string> visited;

        q.push(start);
        visited.push_back(start);

        cout << "BFS: ";

        while (!q.empty()) {
            string current = q.front();
            q.pop();

            cout << current << " -> ";

            for (int i = 0; i < (int)graph[current].size(); i++) {
                string next = graph[current][i];

                if (find(visited.begin(), visited.end(), next)
                    == visited.end()) {
                    visited.push_back(next);
                    q.push(next);
                }
            }
        }

        cout << "END\n";
    }

    void sortByDeadline() {
        vector<Application> apps;

        Node* p = head;

        while (p != NULL) {
            apps.push_back(p->app);
            p = p->next;
        }

        if (apps.empty()) {
            cout << "No applications available.\n";
            return;
        }

        mergeSort<Application>(
            apps, 0, (int)apps.size() - 1, DeadlineLess()
        );

        cout << "\nSORTED APPLICATIONS\n";

        for (int i = 0; i < (int)apps.size(); i++) {
            cout << apps[i].company << " | "
                 << apps[i].role << " | "
                 << apps[i].deadline << endl;
        }
    }

    void recommendJobs() {
        int choice;

        cout << "\n====================================\n";
        cout << " FIND JOBS THAT MATCH YOUR INTEREST\n";
        cout << "====================================\n";
        cout << "Choose the field you are interested in:\n";
        cout << "1. Software Engineering / Programming\n";
        cout << "2. Artificial Intelligence / Machine Learning\n";
        cout << "3. Cybersecurity\n";
        cout << "4. Networking\n";
        cout << "5. Data Science / Data Analytics\n";
        cout << "6. Web Development / Web Design\n";
        cout << "7. Database Management\n";
        cout << "8. Other field\n";
        cout << "Enter your choice: ";

        if (!(cin >> choice)) {
            cin.clear();
            cin.ignore(10000, '\n');
            cout << "Invalid choice. Please enter a number.\n";
            return;
        }
        cin.ignore(10000, '\n');

        cout << "\n====================================\n";
        cout << " POTENTIAL JOBS FOR YOUR FIELD\n";
        cout << "====================================\n";

        if (choice == 1) {
            cout << "\nRecommended job roles:\n";
            cout << "1. Junior Software Developer\n";
            cout << "2. C++ / Java / Python Developer\n";
            cout << "3. Application Developer\n";
            cout << "4. Software QA Tester\n";
            cout << "5. Junior Backend Developer\n";
            cout << "\nUseful skills: programming, OOP, data structures, algorithms, debugging, and Git.\n";
        }
        else if (choice == 2) {
            cout << "\nRecommended job roles:\n";
            cout << "1. Junior AI Developer\n";
            cout << "2. Machine Learning Assistant\n";
            cout << "3. Data Science Intern\n";
            cout << "4. AI Research Assistant\n";
            cout << "5. Junior Data Analyst\n";
            cout << "\nUseful skills: Python, basic statistics, data preparation, machine learning concepts, and model evaluation.\n";
        }
        else if (choice == 3) {
            cout << "\nRecommended job roles:\n";
            cout << "1. Junior Cybersecurity Analyst\n";
            cout << "2. Security Operations Centre (SOC) Analyst\n";
            cout << "3. Information Security Assistant\n";
            cout << "4. IT Security Support Technician\n";
            cout << "5. Junior Risk and Compliance Assistant\n";
            cout << "\nUseful skills: networking basics, operating systems, security principles, risk awareness, and ethical practices.\n";
        }
        else if (choice == 4) {
            cout << "\nRecommended job roles:\n";
            cout << "1. Junior Network Administrator\n";
            cout << "2. Network Support Technician\n";
            cout << "3. IT Support Specialist\n";
            cout << "4. Junior Network Engineer\n";
            cout << "5. Network Operations Centre (NOC) Technician\n";
            cout << "\nUseful skills: TCP/IP, IP addressing, DNS, routing, switching, and troubleshooting.\n";
        }
        else if (choice == 5) {
            cout << "\nRecommended job roles:\n";
            cout << "1. Junior Data Analyst\n";
            cout << "2. Business Intelligence Assistant\n";
            cout << "3. Data Science Intern\n";
            cout << "4. Reporting Analyst\n";
            cout << "5. Junior Database Analyst\n";
            cout << "\nUseful skills: Excel, SQL, statistics, data visualization, and Python.\n";
        }
        else if (choice == 6) {
            cout << "\nRecommended job roles:\n";
            cout << "1. Junior Front-End Developer\n";
            cout << "2. Junior Back-End Developer\n";
            cout << "3. Junior Full-Stack Developer\n";
            cout << "4. Web Designer\n";
            cout << "5. Website Support Assistant\n";
            cout << "\nUseful skills: HTML, CSS, JavaScript, responsive design, web basics, and Git.\n";
        }
        else if (choice == 7) {
            cout << "\nRecommended job roles:\n";
            cout << "1. Junior Database Administrator\n";
            cout << "2. SQL Developer\n";
            cout << "3. Database Support Assistant\n";
            cout << "4. Junior Data Engineer\n";
            cout << "5. Database Analyst\n";
            cout << "\nUseful skills: SQL, database design, tables and relationships, normalization, and backups.\n";
        }
        else if (choice == 8) {
            string field;
            cout << "Enter your field of interest: ";
            getline(cin, field);

            if (field.empty()) {
                cout << "No field entered. Returning to the main menu.\n";
                return;
            }

            cout << "\nExplore entry-level roles related to " << field << ":\n";
            cout << "1. Junior Assistant / Associate\n";
            cout << "2. Intern or Trainee\n";
            cout << "3. Junior Technician or Specialist\n";
            cout << "4. Research or Project Assistant\n";
            cout << "\nCheck job descriptions for " << field
                 << " to find the exact skills and qualifications required.\n";
        }
        else {
            cout << "Invalid choice. Please select a number from 1 to 8.\n";
            return;
        }

        cout << "\nThese are suggested job roles, not confirmed job vacancies.\n";
        cout << "Search for these titles on job websites and check each employer's requirements.\n";
    }

    void interviewAdvice() {
        Node* p = head;
        bool hasInterview = false;

        cout << "\nAPPLICATIONS WITH INTERVIEW STATUS\n";

        while (p != NULL) {
            if (normalizeText(p->app.status) == "interview") {
                cout << "ID: " << p->app.id
                     << " | " << p->app.company
                     << " | " << p->app.role
                     << " | Field: " << p->app.field << endl;

                hasInterview = true;
            }

            p = p->next;
        }

        if (!hasInterview) {
            cout << "There are no applications with Interview status.\n";
            cout << "Update an application's status to Interview first.\n";
            return;
        }

        int id;

        cout << "\nEnter the Application ID you want to prepare for: ";

        if (!(cin >> id)) {
            cin.clear();
            cin.ignore(10000, '\n');
            cout << "Invalid ID. Please enter a number.\n";
            return;
        }

        cin.ignore(10000, '\n');

        p = findID(id);

        if (p == NULL ||
            normalizeText(p->app.status) != "interview") {
            cout << "That ID is not in your interview list.\n";
            return;
        }

        string category = getFieldCategory(p->app.field);

        cout << "\n====================================\n";
        cout << "INTERVIEW PREPARATION GUIDE\n";
        cout << "====================================\n";
        cout << "Company: " << p->app.company << endl;
        cout << "Job Role: " << p->app.role << endl;
        cout << "Field: " << p->app.field << endl;

        cout << "\nFIELD-SPECIFIC PREPARATION\n";

        if (category == "software") {
            cout << "1. Revise programming fundamentals and OOP.\n";
            cout << "2. Practice data structures and algorithms.\n";
            cout << "3. Review your projects and be ready to explain your code.\n";
            cout << "4. Practice solving simple coding problems.\n";
        }
        else if (category == "ai") {
            cout << "1. Revise basic AI and machine learning concepts.\n";
            cout << "2. Understand datasets, data cleaning, and model evaluation.\n";
            cout << "3. Review any AI or machine learning projects you have done.\n";
            cout << "4. Practice explaining how and why a model works.\n";
        }
        else if (category == "cybersecurity") {
            cout << "1. Revise networking and information security basics.\n";
            cout << "2. Understand common security risks and safe practices.\n";
            cout << "3. Review access control, authentication, and encryption concepts.\n";
            cout << "4. Be ready to discuss responsible and ethical decisions.\n";
        }
        else if (category == "networking") {
            cout << "1. Revise the OSI and TCP/IP models.\n";
            cout << "2. Review IP addressing, DNS, and routing basics.\n";
            cout << "3. Understand common network troubleshooting steps.\n";
            cout << "4. Practice explaining how devices communicate.\n";
        }
        else if (category == "datascience") {
            cout << "1. Revise basic statistics and data analysis.\n";
            cout << "2. Practice working with tables, charts, and datasets.\n";
            cout << "3. Review SQL and any data-related projects you have done.\n";
            cout << "4. Practice explaining how you reached a conclusion from data.\n";
        }
        else if (category == "web") {
            cout << "1. Revise HTML, CSS, and JavaScript fundamentals.\n";
            cout << "2. Review responsive design and basic web development concepts.\n";
            cout << "3. Prepare to explain websites or web projects you have built.\n";
            cout << "4. Review how the front end communicates with the back end.\n";
        }
        else if (category == "database") {
            cout << "1. Revise tables, keys, and relationships.\n";
            cout << "2. Practice SQL queries, including SELECT, JOIN, and GROUP BY.\n";
            cout << "3. Understand normalization and basic database design.\n";
            cout << "4. Review a database project you have worked on.\n";
        }
        else {
            cout << "1. Review the main concepts of " << p->app.field << ".\n";
            cout << "2. Read the job description and note its required skills.\n";
            cout << "3. Prepare examples of work or projects related to this field.\n";
            cout << "4. Think of questions you may be asked about this role.\n";
        }

        cout << "\nGENERAL INTERVIEW TIPS\n";
        cout << "1. Learn about the company and the job role.\n";
        cout << "2. Prepare a short introduction about yourself.\n";
        cout << "3. Give clear examples when answering questions.\n";
        cout << "4. Be honest if you do not know an answer.\n";
        cout << "5. Prepare two or three questions to ask the interviewer.\n";
        cout << "\nGood luck with your interview!\n";
    }

    void analytics() {
        cout << "\nAPPLICATION ANALYTICS\n";

        cout << "Total Applications: "
             << countApps(head) << endl;

        cout << "Applied: "
             << countStatus(head, "Applied") << endl;

        cout << "Interviews: "
             << countStatus(head, "Interview") << endl;

        cout << "Rejected: "
             << countStatus(head, "Rejected") << endl;

        int total = countApps(head);
        int interviews = countStatus(head, "Interview");
        int selected = countStatus(head, "Selected");

        cout << "Selected: " << selected << endl;

        if (total == 0) {
            cout << "Selection Success Rate: 0%\n";
            cout << "Interview Rate: 0%\n";
        }
        else {
            cout << "Selection Success Rate: "
                 << (selected * 100.0 / total) << "%\n";

            cout << "Interview Rate: "
                 << (interviews * 100.0 / total) << "%\n";
        }
    }
};

int main() {
    JobTracker tracker;
    int choice;

    do {
        cout << "\n====================================\n";
        cout << " JOB APPLICATION TRACKING SYSTEM\n";
        cout << "====================================\n";

        cout << "1. Add Application\n";
        cout << "2. Display Applications\n";
        cout << "3. Search Company (Hashing)\n";
        cout << "4. Search Company (Binary Search)\n";
        cout << "5. View Deadlines (BST)\n";
        cout << "6. View Urgency Ranking (Min-Heap)\n";
        cout << "7. Update Application Status\n";
        cout << "8. Undo Last Operation (Stack)\n";
        cout << "9. View Interview Queue\n";
        cout << "10. Process Next Interview\n";
        cout << "11. Add Company Connection (Graph)\n";
        cout << "12. BFS Traversal\n";
        cout << "13. Sort by Deadline (Merge Sort)\n";
        cout << "14. Application Analytics\n";
        cout << "15. Field-Based Job Recommendations\n";
        cout << "16. Interview Preparation Advice\n";
        cout << "0. Exit\n";

        cout << "Enter choice: ";

        if (!(cin >> choice)) {
            cin.clear();
            cin.ignore(10000, '\n');

            cout << "Enter a valid number.\n";
            continue;
        }

        cin.ignore(10000, '\n');

        switch (choice) {
            case 1:
                tracker.addApplication();
                break;

            case 2:
                tracker.display();
                break;

            case 3:
                tracker.searchCompany();
                break;

            case 4:
                tracker.binarySearchCompany();
                break;

            case 5:
                tracker.showDeadlines();
                break;

            case 6:
                tracker.showUrgency();
                break;

            case 7:
                tracker.updateStatus();
                break;

            case 8:
                tracker.undo();
                break;

            case 9:
                tracker.showQueue();
                break;

            case 10:
                tracker.processInterview();
                break;

            case 11:
                tracker.addConnection();
                break;

            case 12:
                tracker.BFS();
                break;

            case 13:
                tracker.sortByDeadline();
                break;

            case 14:
                tracker.analytics();
                break;

            case 15:
                tracker.recommendJobs();
                break;

            case 16:
                tracker.interviewAdvice();
                break;

            case 0:
                cout << "Thank you for using the system!\n";
                break;

            default:
                cout << "Invalid choice.\n";
        }

    } while (choice != 0);

    return 0;
}

