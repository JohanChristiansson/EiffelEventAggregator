package mypackage;

import java.util.Objects;

public class Event {
    private String id;
    private String type;
    private long timestamp;
    private String [] links;

    // No-argument constructor (required for POJO)
    public Event() {}

    // Constructor
    public Event(String id, String type, long timestamp, String [] links) {
        this.id = id;
        this.type = type;
        this.timestamp = timestamp;
        this.links = links;

    }
    // Getters and setters
    public String getId() {
        return this.id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String[] getLinks() {
        return links;
    }

    public void setLinks(String[] links) {
        this.links = links;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }

    @Override
    public String toString() {
        return "Event{" +
                "id=" + id +
                ", type='" + type + '\'' +
                ", timestamp=" + timestamp +
                '}';
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Event event = (Event) o;
        return Objects.equals(id, event.id) &&
                timestamp == event.timestamp &&
                Objects.equals(type, event.type);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, type, timestamp);
    }
}
