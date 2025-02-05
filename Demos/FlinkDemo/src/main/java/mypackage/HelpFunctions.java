package mypackage;

public class HelpFunctions {
    //Check link between two events
    public static boolean linksToEvent(Event sourceEvent, Event targetEvent, String linkType) {
        for (Event.Link link : sourceEvent.getLinks()) {
            if (link.getTarget().equals(targetEvent.getMeta().getId()) && link.getType().equals(linkType)) {
                return true;
            }
        }
        return false;
    }
}
