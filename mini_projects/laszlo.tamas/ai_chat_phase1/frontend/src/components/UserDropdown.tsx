import { User } from "../types";

interface UserDropdownProps {
  users: User[];
  selectedUserId: number | null;
  onUserChange: (userId: number) => void;
}

export const UserDropdown = ({
  users,
  selectedUserId,
  onUserChange,
}: UserDropdownProps) => {
  return (
    <div className="user-dropdown">
      <label htmlFor="user-select">Select User: </label>
      <select
        id="user-select"
        value={selectedUserId || ""}
        onChange={(e) => onUserChange(Number(e.target.value))}
      >
        <option value="">-- Choose a user --</option>
        {users.map((user) => (
          <option
            key={user.user_id}
            value={user.user_id}
            disabled={!user.is_active}
          >
            {user.firstname} {user.lastname} ({user.nickname})
            {!user.is_active && " - INACTIVE"}
          </option>
        ))}
      </select>
    </div>
  );
};
