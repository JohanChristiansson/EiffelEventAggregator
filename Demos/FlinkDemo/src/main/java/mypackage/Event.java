
package mypackage;

import java.util.Objects;

import java.util.List;

public class Event {
    private Meta meta;
    private Data data;
    private List<Link> links; // List of links, each link contains target and type

    public Event() {}  // No-arg constructor

    public Meta getMeta() { return meta; }
    public void setMeta(Meta meta) { this.meta = meta; }

    public Data getData() { return data; }
    public void setData(Data data) { this.data = data; }

    public List<Link> getLinks() { return links; }
    public void setLinks(List<Link> links) { this.links = links; }

    // --- Nested Classes (Non-static) ---
    public class Meta {
        private long time;
        private String id;
        private String version;
        private String type;
        private Source source;

        public Meta() {}

        public long getTime() { return time; }
        public void setTime(long time) { this.time = time; }

        public String getId() { return id; }
        public void setId(String id) { this.id = id; }

        public String getVersion() { return version; }
        public void setVersion(String version) { this.version = version; }

        public String getType() { return type; }
        public void setType(String type) { this.type = type; }

        public Source getSource() { return source; }
        public void setSource(Source source) { this.source = source; }
    }

    public static class Source {
        private String domainId;

        public Source() {}

        public String getDomainId() { return domainId; }
        public void setDomainId(String domainId) { this.domainId = domainId; }
    }

    public class Data {
        private List<CustomData> customData;
        private Submitter submitter;
        private GitIdentifier gitIdentifier;

        public Data() {}

        public List<CustomData> getCustomData() { return customData; }
        public void setCustomData(List<CustomData> customData) { this.customData = customData; }

        public Submitter getSubmitter() { return submitter; }
        public void setSubmitter(Submitter submitter) { this.submitter = submitter; }

        public GitIdentifier getGitIdentifier() { return gitIdentifier; }
        public void setGitIdentifier(GitIdentifier gitIdentifier) { this.gitIdentifier = gitIdentifier; }
    }

    public static class CustomData {
        private String key;
        private String value;  // Changed from Object to String

        public CustomData() {}

        public String getKey() { return key; }
        public void setKey(String key) { this.key = key; }

        public String getValue() { return value; }
        public void setValue(String value) { this.value = value; }
    }

    public static class Submitter {
        private String name;
        private String email;
        private String group;
        private String id;

        public Submitter() {}

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }

        public String getEmail() { return email; }
        public void setEmail(String email) { this.email = email; }

        public String getGroup() { return group; }
        public void setGroup(String group) { this.group = group; }

        public String getId() { return id; }
        public void setId(String id) { this.id = id; }
    }

    public static class GitIdentifier {
        private String commitId;
        private String repoName;
        private String branch;
        private String repoUri;

        public GitIdentifier() {}

        public String getCommitId() { return commitId; }
        public void setCommitId(String commitId) { this.commitId = commitId; }

        public String getRepoName() { return repoName; }
        public void setRepoName(String repoName) { this.repoName = repoName; }

        public String getBranch() { return branch; }
        public void setBranch(String branch) { this.branch = branch; }

        public String getRepoUri() { return repoUri; }
        public void setRepoUri(String repoUri) { this.repoUri = repoUri; }
    }

    // --- Updated Link class ---
    public static class Link {
        private String target;
        private String type;

        public Link() {}

        public String getTarget() { return target; }
        public void setTarget(String target) { this.target = target; }

        public String getType() { return type; }
        public void setType(String type) { this.type = type; }
    }
}
